#!/usr/bin/env python3
"""
Direct CLI runner for Concord pipeline integration.

This is the simpler approach — Concord runs this script as a task directly,
no API server needed. It clones the repo, runs the ADK migration agents,
commits, and pushes to a new branch.

Usage (from Concord or command line):
    python concord_runner.py \
        --repo-url https://github.com/myorg/puppet-webapp.git \
        --source-branch main \
        --target-branch puppet8-migration/main/20260222 \
        --module-path . \
        --pattern migrator \
        --push

Environment Variables (set in Concord secrets or task config):
    GOOGLE_API_KEY           — Required. Google AI Studio or Vertex AI key.
    GOOGLE_GENAI_USE_VERTEXAI — "0" for AI Studio, "1" for Vertex AI.
    GIT_TOKEN                — Optional. GitHub PAT for private repos.
    GIT_AUTHOR_NAME          — Optional. Default: "puppet8-migrator-concord".
    GIT_AUTHOR_EMAIL         — Optional. Default: "puppet8-migrator@noreply".

Exit codes:
    0 — Success (migration complete, branch pushed)
    1 — Failure (error during migration)
    2 — No changes detected (module may already be compatible)
"""

import argparse
import asyncio
import importlib
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Setup path for ADK agent imports
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR / "adk_migrator"))

load_dotenv(SCRIPT_DIR / "adk_migrator" / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("concord-puppet8-migrator")


# ─────────────────────────────────────────────────────────────────────
# Git Operations
# ─────────────────────────────────────────────────────────────────────

def git_cmd(repo_dir: Path, *args: str, env: dict | None = None) -> str:
    """Run a git command in the given repo directory."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    result = subprocess.run(
        ["git", "-C", str(repo_dir)] + list(args),
        capture_output=True,
        text=True,
        timeout=120,
        env=full_env,
    )
    if result.returncode != 0:
        logger.error(f"git {' '.join(args)} failed:\n{result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, f"git {' '.join(args)}", result.stderr)
    return result.stdout.strip()


def clone_repo(repo_url: str, branch: str, work_dir: Path) -> Path:
    """Clone the repository."""
    token = os.environ.get("GIT_TOKEN", "")
    clone_url = repo_url
    if token and clone_url.startswith("https://"):
        clone_url = clone_url.replace("https://", f"https://{token}@", 1)

    repo_dir = work_dir / "repo"
    logger.info(f"Cloning {repo_url} (branch: {branch})")

    subprocess.run(
        ["git", "clone", "--branch", branch, "--single-branch", "--depth", "50",
         clone_url, str(repo_dir)],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    logger.info("Clone complete")
    return repo_dir


# ─────────────────────────────────────────────────────────────────────
# File Operations
# ─────────────────────────────────────────────────────────────────────

def collect_puppet_files(module_root: Path) -> dict[str, str]:
    """Collect all Puppet-relevant files."""
    files = {}
    extensions = {".pp", ".rb", ".yaml", ".yml", ".erb", ".epp", ".json"}
    skip_dirs = {".git", ".vagrant", "vendor", "pkg", ".bundle", "spec/fixtures"}

    for path in module_root.rglob("*"):
        rel = path.relative_to(module_root)
        if any(part in skip_dirs for part in rel.parts):
            continue
        if path.is_file() and path.suffix in extensions:
            files[str(rel)] = path.read_text(errors="replace")

    return files


def format_files_prompt(files: dict[str, str]) -> str:
    """Format files into the agent prompt format."""
    parts = []
    for fp, content in sorted(files.items()):
        parts.append(f"--- FILE: {fp} ---\n{content}\n--- END FILE: {fp} ---\n")
    return "\n".join(parts)


def extract_migrated_files(output: str) -> dict[str, str]:
    """Parse agent output to extract migrated file contents."""
    files = {}
    current_file = None
    current_lines = []

    for line in output.split("\n"):
        if line.startswith("--- BEGIN FILE:") or line.startswith("--- FILE:"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                current_file = parts[1].strip().rstrip(" -").strip()
                current_lines = []
        elif line.startswith("--- END FILE:") or line.startswith("--- END"):
            if current_file and current_lines:
                files[current_file] = "\n".join(current_lines)
            current_file = None
            current_lines = []
        elif current_file is not None:
            current_lines.append(line)

    if current_file and current_lines:
        files[current_file] = "\n".join(current_lines)

    return files


def write_migrated_files(repo_dir: Path, module_path: str, migrated_files: dict[str, str]):
    """Write migrated files back to the repo."""
    root = repo_dir / module_path if module_path != "." else repo_dir
    for rel_path, content in migrated_files.items():
        target = root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        logger.info(f"  Wrote: {rel_path}")


# ─────────────────────────────────────────────────────────────────────
# ADK Agent Runner
# ─────────────────────────────────────────────────────────────────────

async def run_adk_agent(pattern: str, prompt: str) -> dict[str, str]:
    """Run the specified ADK agent and return results."""
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    agent_module = importlib.import_module(f"{pattern}_pattern.agent")
    agent = agent_module.root_agent

    runner = InMemoryRunner(agent=agent, app_name="puppet8_concord")
    user_id = f"concord_{uuid.uuid4().hex[:8]}"

    session = await runner.session_service.create_session(
        app_name="puppet8_concord",
        user_id=user_id,
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)],
    )

    full_output = []
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=user_message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    full_output.append(part.text)
                    # Stream output to Concord logs in real-time
                    print(part.text, end="", flush=True)

    print()  # Final newline

    # Get session state
    final_session = await runner.session_service.get_session(
        app_name="puppet8_concord",
        user_id=user_id,
        session_id=session.id,
    )

    result = {"agent_output": "\n".join(full_output)}
    if final_session and final_session.state:
        for key, value in final_session.state.items():
            result[key] = str(value)

    return result


# ─────────────────────────────────────────────────────────────────────
# Main Pipeline
# ─────────────────────────────────────────────────────────────────────

async def run_pipeline(args: argparse.Namespace) -> int:
    """Execute the full migration pipeline. Returns exit code."""
    work_dir = Path(tempfile.mkdtemp(prefix="puppet8-concord-"))
    report = {"status": "started", "repo": args.repo_url, "branch": args.source_branch}

    try:
        # 1. Clone
        repo_dir = clone_repo(args.repo_url, args.source_branch, work_dir)

        # 2. Collect files
        module_root = repo_dir / args.module_path if args.module_path != "." else repo_dir
        if not module_root.exists():
            dirs = [d.name for d in repo_dir.iterdir() if d.is_dir() and d.name != ".git"]
            logger.error(f"Module path '{args.module_path}' not found. Available: {dirs}")
            report["status"] = "failed"
            report["error"] = f"Module path not found: {args.module_path}"
            return 1

        puppet_files = collect_puppet_files(module_root)
        logger.info(f"Collected {len(puppet_files)} Puppet files:")
        for f in sorted(puppet_files.keys()):
            logger.info(f"  {f}")

        if not puppet_files:
            logger.error("No Puppet files found in the specified module path.")
            report["status"] = "failed"
            report["error"] = "No Puppet files found"
            return 1

        report["files_found"] = len(puppet_files)

        # 3. Run ADK agent
        file_content = format_files_prompt(puppet_files)

        prompt_templates = {
            "analyzer": (
                "Analyze the following Puppet 7 module for ALL Puppet 8 compatibility issues.\n\n"
            ),
            "migrator": (
                "Migrate the following Puppet 7 module to Puppet 8. Apply ALL changes: "
                "legacy facts → structured facts, deprecated functions → modern replacements, "
                "add type annotations, convert hiera v3 → v5, fix Ruby 3.2 compatibility. "
                "Output complete migrated files.\n\n"
            ),
            "validator": (
                "Validate and iteratively fix the following Puppet code for Puppet 8.\n\n"
            ),
        }

        prompt = prompt_templates.get(args.pattern, prompt_templates["migrator"]) + file_content
        logger.info(f"Running ADK agent: {args.pattern} (prompt: {len(prompt)} chars)")

        agent_result = await run_adk_agent(args.pattern, prompt)
        logger.info(f"Agent finished. Output keys: {list(agent_result.keys())}")

        # 4. Extract and write migrated files
        if args.pattern in ("migrator", "validator"):
            output_text = (
                agent_result.get("final_output")
                or agent_result.get("current_code")
                or agent_result.get("agent_output", "")
            )
            migrated_files = extract_migrated_files(output_text)

            if not migrated_files:
                logger.warning("Could not extract migrated files from agent output.")
                logger.info("Agent raw output saved to report for debugging.")
                report["status"] = "partial"
                report["warning"] = "Agent ran but file extraction failed"
                report["raw_output_length"] = len(output_text)

                # Write raw output for debugging
                raw_out = work_dir / "agent_output.txt"
                raw_out.write_text(output_text)
                logger.info(f"Raw output: {raw_out}")
                return 1

            logger.info(f"Extracted {len(migrated_files)} migrated files")
            write_migrated_files(repo_dir, args.module_path, migrated_files)
            report["files_migrated"] = len(migrated_files)

            # 5. Create branch, commit, push
            target_branch = args.target_branch or (
                f"puppet8-migration/{args.source_branch}/"
                f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
            )

            git_env = {
                "GIT_AUTHOR_NAME": os.environ.get("GIT_AUTHOR_NAME", "puppet8-migrator-concord"),
                "GIT_AUTHOR_EMAIL": os.environ.get("GIT_AUTHOR_EMAIL", "puppet8-migrator@noreply"),
                "GIT_COMMITTER_NAME": os.environ.get("GIT_AUTHOR_NAME", "puppet8-migrator-concord"),
                "GIT_COMMITTER_EMAIL": os.environ.get("GIT_AUTHOR_EMAIL", "puppet8-migrator@noreply"),
            }

            git_cmd(repo_dir, "checkout", "-b", target_branch, env=git_env)
            git_cmd(repo_dir, "add", "-A", env=git_env)

            status = git_cmd(repo_dir, "status", "--porcelain", env=git_env)
            if not status:
                logger.info("No changes detected — module may already be Puppet 8 compatible.")
                report["status"] = "no_changes"
                return 2

            change_count = len(status.strip().split("\n"))
            report["changes"] = change_count

            commit_msg = (
                f"puppet8-migration: Migrate {args.module_path} from Puppet 7 to 8\n\n"
                f"Automated migration by puppet8-migrator ADK pipeline.\n"
                f"Pattern: {args.pattern}\n"
                f"Files analyzed: {len(puppet_files)}\n"
                f"Files migrated: {len(migrated_files)}\n"
                f"Source: {args.source_branch}\n"
                f"Changes:\n"
                f"  - Legacy facts → structured facts\n"
                f"  - Deprecated stdlib functions → modern replacements\n"
                f"  - Added Puppet type annotations\n"
                f"  - Hiera v3 → v5 configuration\n"
                f"  - Ruby 3.2 compatibility (File.exist?, ENV[])\n"
                f"  - Strict mode compliance\n"
            )

            git_cmd(repo_dir, "commit", "-m", commit_msg, env=git_env)
            commit_hash = git_cmd(repo_dir, "rev-parse", "HEAD", env=git_env)
            report["commit"] = commit_hash
            report["branch"] = target_branch

            if args.push:
                logger.info(f"Pushing branch '{target_branch}' to origin...")
                git_cmd(repo_dir, "push", "-u", "origin", target_branch, env=git_env)
                report["pushed"] = True
                logger.info(f"Branch pushed successfully: {target_branch}")
            else:
                report["pushed"] = False
                logger.info(f"Dry-run mode — branch '{target_branch}' NOT pushed.")

            report["status"] = "success"

        elif args.pattern == "analyzer":
            # Analysis only — no file changes, just report
            report["status"] = "analysis_complete"
            for key in ("manifest_analysis", "ruby_analysis", "hiera_analysis", "template_analysis"):
                if key in agent_result:
                    report[key] = agent_result[key][:3000]

        # Write report JSON for Concord to pick up
        report_file = Path(os.environ.get("CONCORD_REPORT_DIR", work_dir)) / "migration_report.json"
        report_file.write_text(json.dumps(report, indent=2))
        logger.info(f"Report written: {report_file}")

        # Also write to stdout for Concord log capture
        print("\n" + "=" * 70)
        print("MIGRATION REPORT")
        print("=" * 70)
        print(json.dumps(report, indent=2))

        return 0

    except Exception as e:
        logger.exception("Pipeline failed")
        report["status"] = "failed"
        report["error"] = f"{type(e).__name__}: {str(e)}"

        report_file = Path(os.environ.get("CONCORD_REPORT_DIR", work_dir)) / "migration_report.json"
        report_file.write_text(json.dumps(report, indent=2))

        return 1

    finally:
        if not os.environ.get("KEEP_WORK_DIR"):
            shutil.rmtree(work_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(
        description="Puppet 7→8 Migration — Concord CLI Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full migration with push
  python concord_runner.py \\
      --repo-url https://github.com/myorg/puppet-webapp.git \\
      --source-branch main \\
      --pattern migrator \\
      --push

  # Analysis only (no changes)
  python concord_runner.py \\
      --repo-url https://github.com/myorg/puppet-webapp.git \\
      --pattern analyzer

  # Migrate a specific module in a control repo
  python concord_runner.py \\
      --repo-url https://github.com/myorg/puppet-control.git \\
      --source-branch production \\
      --module-path modules/webapp \\
      --target-branch puppet8/webapp \\
      --push
        """,
    )
    parser.add_argument("--repo-url", required=True, help="GitHub repo clone URL (HTTPS)")
    parser.add_argument("--source-branch", default="main", help="Branch to migrate from (default: main)")
    parser.add_argument("--target-branch", default=None, help="Target branch name (default: auto-generated)")
    parser.add_argument("--module-path", default=".", help="Path to Puppet module within repo (default: .)")
    parser.add_argument(
        "--pattern",
        choices=["analyzer", "migrator", "validator"],
        default="migrator",
        help="ADK pattern: migrator (full pipeline), analyzer (report), validator (iterative fix)",
    )
    parser.add_argument("--push", action="store_true", help="Push migrated branch to origin")
    parser.add_argument("--no-push", dest="push", action="store_false", help="Dry-run, do not push")
    parser.set_defaults(push=False)

    args = parser.parse_args()

    exit_code = asyncio.run(run_pipeline(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
