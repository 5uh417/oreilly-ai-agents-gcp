#!/usr/bin/env python3
"""
Concord CLI runner that delegates to an external `adk api_server` via /run.

Unlike concord_runner.py (which embeds InMemoryRunner and runs the agents
in-process), this script treats the ADK server as a remote service.
The ADK server can live anywhere — same host, a k8s pod, a shared VM — and
this script handles the git clone / file extraction / commit / push plumbing
around it.

Flow:
  1. Clone the target Puppet module repo
  2. Collect all Puppet files into a single prompt
  3. POST the prompt to the ADK api_server /run endpoint
  4. Parse the migrated files out of the response events
  5. Write them back to the cloned repo
  6. Branch, commit, push

Usage:
    python concord_adk_runner.py \
        --adk-url http://localhost:8090 \
        --app-name migrator_pattern \
        --repo-url https://github.com/myorg/puppet-webapp.git \
        --source-branch main \
        --target-branch puppet8/webapp \
        --push

Environment Variables:
    ADK_SERVER_URL           — Alternative to --adk-url flag.
    GIT_TOKEN                — GitHub PAT for private repos.
    GIT_AUTHOR_NAME          — Git commit author. Default: "puppet8-migrator-adk".
    GIT_AUTHOR_EMAIL         — Git commit email. Default: "puppet8-migrator@noreply".

Exit codes:
    0 — Migration complete, branch pushed (or dry-run committed locally)
    1 — Failure (clone, ADK call, parse, or push error)
    2 — No changes detected after migration
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("concord-adk-runner")


# ─────────────────────────────────────────────────────────────────────
# Git helpers
# ─────────────────────────────────────────────────────────────────────

def git_cmd(repo_dir: Path, *args: str) -> str:
    """Run a git command and return stdout."""
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = os.environ.get("GIT_AUTHOR_NAME", "puppet8-migrator-adk")
    env["GIT_AUTHOR_EMAIL"] = os.environ.get("GIT_AUTHOR_EMAIL", "puppet8-migrator@noreply")
    env["GIT_COMMITTER_NAME"] = env["GIT_AUTHOR_NAME"]
    env["GIT_COMMITTER_EMAIL"] = env["GIT_AUTHOR_EMAIL"]

    result = subprocess.run(
        ["git", "-C", str(repo_dir)] + list(args),
        capture_output=True, text=True, timeout=120, env=env,
    )
    if result.returncode != 0:
        logger.error(f"git {' '.join(args)}: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, f"git {' '.join(args)}", result.stderr)
    return result.stdout.strip()


def clone_repo(repo_url: str, branch: str, work_dir: Path) -> Path:
    """Clone the repo into work_dir."""
    token = os.environ.get("GIT_TOKEN", "")
    clone_url = repo_url
    if token and clone_url.startswith("https://"):
        clone_url = clone_url.replace("https://", f"https://{token}@", 1)

    repo_dir = work_dir / "repo"
    logger.info(f"Cloning {repo_url} (branch: {branch})")
    subprocess.run(
        ["git", "clone", "--branch", branch, "--single-branch", "--depth", "50",
         clone_url, str(repo_dir)],
        check=True, capture_output=True, text=True, timeout=120,
    )
    return repo_dir


# ─────────────────────────────────────────────────────────────────────
# File collection
# ─────────────────────────────────────────────────────────────────────

PUPPET_EXTENSIONS = {".pp", ".rb", ".yaml", ".yml", ".erb", ".epp", ".json"}
SKIP_DIRS = {".git", ".vagrant", "vendor", "pkg", ".bundle", "spec/fixtures"}


def collect_puppet_files(module_root: Path) -> dict[str, str]:
    """Walk the module tree and collect Puppet-relevant files."""
    files = {}
    for path in module_root.rglob("*"):
        rel = path.relative_to(module_root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.is_file() and path.suffix in PUPPET_EXTENSIONS:
            files[str(rel)] = path.read_text(errors="replace")
    return files


def format_prompt(files: dict[str, str], pattern: str) -> str:
    """Build the agent prompt from collected files."""
    file_block = "\n".join(
        f"--- FILE: {fp} ---\n{content}\n--- END FILE: {fp} ---\n"
        for fp, content in sorted(files.items())
    )

    preambles = {
        "analyzer_pattern": (
            "Analyze the following Puppet 7 module for ALL Puppet 8 compatibility issues. "
            "Check manifests, Ruby code, Hiera config, and templates. "
            "Produce a detailed report for each file.\n\n"
        ),
        "migrator_pattern": (
            "Migrate the following Puppet 7 module to be fully Puppet 8 compatible. "
            "Apply ALL changes: legacy facts → structured facts, deprecated functions → "
            "modern replacements, add type annotations to every parameter, convert "
            "hiera v3 → v5, fix Ruby 3.2 compatibility. "
            "Output the COMPLETE migrated files using the markers:\n"
            "--- BEGIN FILE: <path> ---\n<content>\n--- END FILE: <path> ---\n\n"
        ),
        "validator_pattern": (
            "Validate and iteratively fix the following Puppet code until it passes "
            "all Puppet 8 compatibility checks.\n\n"
        ),
        "coordinator_pattern": (
            "Migrate this Puppet file to Puppet 8. Route to the appropriate specialist.\n\n"
        ),
    }

    preamble = preambles.get(pattern, preambles["migrator_pattern"])
    return preamble + file_block


# ─────────────────────────────────────────────────────────────────────
# ADK api_server interaction
# ─────────────────────────────────────────────────────────────────────

def call_adk_run(adk_url: str, app_name: str, prompt: str, timeout: int = 600) -> list[dict]:
    """
    POST to the ADK api_server /run endpoint and return the event list.

    The /run endpoint is synchronous — it blocks until the full agent
    execution completes and returns all events as a JSON array.
    """
    url = f"{adk_url.rstrip('/')}/run"
    session_id = f"concord_{int(time.time())}"
    user_id = "concord_pipeline"

    payload = {
        "appName": app_name,
        "userId": user_id,
        "sessionId": session_id,
        "newMessage": {
            "role": "user",
            "parts": [{"text": prompt}],
        },
        "streaming": False,
    }

    body = json.dumps(payload).encode("utf-8")

    logger.info(f"POST {url}")
    logger.info(f"  appName={app_name}  userId={user_id}  sessionId={session_id}")
    logger.info(f"  prompt length: {len(prompt)} chars")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            resp_body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        logger.error(f"ADK server returned HTTP {e.code}: {error_body}")
        raise RuntimeError(f"ADK api_server error (HTTP {e.code}): {error_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot reach ADK api_server at {adk_url}: {e.reason}")

    logger.info(f"ADK response: HTTP {status}, {len(resp_body)} bytes")

    events = json.loads(resp_body)
    if not isinstance(events, list):
        events = [events]

    return events


def call_adk_run_sse(adk_url: str, app_name: str, prompt: str, timeout: int = 600) -> list[dict]:
    """
    POST to the ADK api_server /run_sse endpoint and stream events.

    Falls back to /run if SSE is not available.
    Returns collected events as a list.
    """
    url = f"{adk_url.rstrip('/')}/run_sse"
    session_id = f"concord_{int(time.time())}"
    user_id = "concord_pipeline"

    payload = {
        "appName": app_name,
        "userId": user_id,
        "sessionId": session_id,
        "newMessage": {
            "role": "user",
            "parts": [{"text": prompt}],
        },
        "streaming": True,
    }

    body = json.dumps(payload).encode("utf-8")

    logger.info(f"POST {url} (SSE streaming)")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )

    events = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            buffer = ""
            for chunk in iter(lambda: resp.read(4096), b""):
                buffer += chunk.decode("utf-8", errors="replace")
                while "\n\n" in buffer:
                    event_block, buffer = buffer.split("\n\n", 1)
                    for line in event_block.split("\n"):
                        if line.startswith("data: "):
                            data_str = line[6:]
                            try:
                                event = json.loads(data_str)
                                events.append(event)
                                # Stream text to stdout for Concord logs
                                if isinstance(event, dict):
                                    content = event.get("content", {})
                                    parts = content.get("parts", []) if isinstance(content, dict) else []
                                    for part in parts:
                                        if isinstance(part, dict) and "text" in part:
                                            print(part["text"], end="", flush=True)
                            except json.JSONDecodeError:
                                pass
            print()  # Final newline
    except urllib.error.HTTPError:
        logger.warning("SSE endpoint not available, falling back to /run")
        return call_adk_run(adk_url, app_name, prompt, timeout)
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot reach ADK api_server at {adk_url}: {e.reason}")

    return events


def extract_text_from_events(events: list[dict]) -> str:
    """Pull all text content out of ADK response events."""
    texts = []
    for event in events:
        if not isinstance(event, dict):
            continue

        # Handle nested content.parts structure
        content = event.get("content", {})
        if isinstance(content, dict):
            parts = content.get("parts", [])
            for part in parts:
                if isinstance(part, dict) and "text" in part:
                    texts.append(part["text"])

        # Handle flat text field
        if "text" in event:
            texts.append(event["text"])

        # Handle actions/state in some event formats
        if "actions" in event and isinstance(event["actions"], dict):
            state_delta = event["actions"].get("stateDelta", {})
            for key in ("final_output", "migrated_code", "current_code"):
                if key in state_delta:
                    texts.append(str(state_delta[key]))

    return "\n".join(texts)


# ─────────────────────────────────────────────────────────────────────
# File extraction from agent output
# ─────────────────────────────────────────────────────────────────────

def extract_migrated_files(text: str) -> dict[str, str]:
    """Parse --- BEGIN FILE / --- END FILE markers from agent output."""
    files = {}
    current_file = None
    current_lines: list[str] = []

    for line in text.split("\n"):
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
    """Overwrite repo files with migrated content."""
    root = repo_dir / module_path if module_path != "." else repo_dir
    for rel_path, content in migrated_files.items():
        target = root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        logger.info(f"  Wrote: {rel_path}")


# ─────────────────────────────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────────────────────────────

def run_pipeline(args: argparse.Namespace) -> int:
    """Execute the full clone → ADK call → commit → push pipeline."""
    work_dir = Path(tempfile.mkdtemp(prefix="puppet8-adk-"))
    report: dict = {
        "status": "started",
        "mode": "adk_api_server",
        "adk_url": args.adk_url,
        "app_name": args.app_name,
        "repo": args.repo_url,
        "source_branch": args.source_branch,
    }

    try:
        # ── 1. Clone ──
        repo_dir = clone_repo(args.repo_url, args.source_branch, work_dir)
        logger.info("Clone complete")

        # ── 2. Collect files ──
        module_root = repo_dir / args.module_path if args.module_path != "." else repo_dir
        if not module_root.exists():
            dirs = [d.name for d in repo_dir.iterdir() if d.is_dir() and d.name != ".git"]
            logger.error(f"Module path '{args.module_path}' not found. Available: {dirs}")
            return 1

        puppet_files = collect_puppet_files(module_root)
        logger.info(f"Collected {len(puppet_files)} Puppet files")
        for f in sorted(puppet_files):
            logger.info(f"  {f}")

        if not puppet_files:
            logger.error("No Puppet files found.")
            return 1

        report["files_found"] = len(puppet_files)

        # ── 3. Build prompt and call ADK api_server ──
        prompt = format_prompt(puppet_files, args.app_name)
        logger.info(f"Prompt: {len(prompt)} chars → ADK {args.adk_url} ({args.app_name})")

        if args.stream:
            events = call_adk_run_sse(args.adk_url, args.app_name, prompt, timeout=args.timeout)
        else:
            events = call_adk_run(args.adk_url, args.app_name, prompt, timeout=args.timeout)

        logger.info(f"Received {len(events)} events from ADK")

        # ── 4. Extract text from events ──
        full_text = extract_text_from_events(events)
        logger.info(f"Extracted {len(full_text)} chars of text from response")

        if not full_text:
            logger.error("ADK returned no text content. Raw events dumped below.")
            print(json.dumps(events, indent=2, default=str)[:5000])
            return 1

        # Save raw output for debugging
        raw_out = work_dir / "adk_response.txt"
        raw_out.write_text(full_text)

        # ── 5. For analysis-only, just report ──
        if args.app_name == "analyzer_pattern":
            report["status"] = "analysis_complete"
            report["analysis_length"] = len(full_text)
            print("\n" + "=" * 70)
            print("ANALYSIS REPORT")
            print("=" * 70)
            print(full_text[:10000])
            if len(full_text) > 10000:
                print(f"\n... ({len(full_text) - 10000} more chars, see adk_response.txt)")
            _write_report(report, work_dir)
            return 0

        # ── 6. Parse migrated files ──
        migrated_files = extract_migrated_files(full_text)

        if not migrated_files:
            logger.warning("Could not parse migrated files from agent output.")
            logger.info(f"Raw output saved to: {raw_out}")
            logger.info("First 500 chars of output:")
            print(full_text[:500])
            report["status"] = "parse_failed"
            _write_report(report, work_dir)
            return 1

        logger.info(f"Parsed {len(migrated_files)} migrated files:")
        for f in sorted(migrated_files):
            logger.info(f"  {f}")
        report["files_migrated"] = len(migrated_files)

        # ── 7. Write files back to repo ──
        write_migrated_files(repo_dir, args.module_path, migrated_files)

        # ── 8. Branch, commit, push ──
        target_branch = args.target_branch or (
            f"puppet8-migration/{args.source_branch}/"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        )

        git_cmd(repo_dir, "checkout", "-b", target_branch)
        git_cmd(repo_dir, "add", "-A")

        status = git_cmd(repo_dir, "status", "--porcelain")
        if not status:
            logger.info("No changes detected — module may already be Puppet 8 compatible.")
            report["status"] = "no_changes"
            _write_report(report, work_dir)
            return 2

        change_count = len(status.strip().split("\n"))
        report["changes"] = change_count
        report["branch"] = target_branch

        commit_msg = (
            f"puppet8-migration: Migrate {args.module_path} from Puppet 7 to 8\n\n"
            f"Automated migration via ADK api_server ({args.adk_url}).\n"
            f"Agent pattern: {args.app_name}\n"
            f"Files analyzed: {len(puppet_files)}\n"
            f"Files migrated: {len(migrated_files)}\n"
            f"Source: {args.source_branch}\n"
        )

        git_cmd(repo_dir, "commit", "-m", commit_msg)
        commit_hash = git_cmd(repo_dir, "rev-parse", "HEAD")
        report["commit"] = commit_hash

        if args.push:
            logger.info(f"Pushing branch '{target_branch}' to origin")
            git_cmd(repo_dir, "push", "-u", "origin", target_branch)
            report["pushed"] = True
            logger.info("Push complete")
        else:
            report["pushed"] = False
            logger.info(f"Dry-run — branch '{target_branch}' NOT pushed")

        report["status"] = "success"
        _write_report(report, work_dir)

        print("\n" + "=" * 70)
        print("MIGRATION REPORT")
        print("=" * 70)
        print(json.dumps(report, indent=2))

        return 0

    except Exception as e:
        logger.exception("Pipeline failed")
        report["status"] = "failed"
        report["error"] = f"{type(e).__name__}: {e}"
        _write_report(report, work_dir)
        return 1

    finally:
        if not os.environ.get("KEEP_WORK_DIR"):
            shutil.rmtree(work_dir, ignore_errors=True)


def _write_report(report: dict, work_dir: Path):
    """Write JSON report to Concord attachments dir or work_dir."""
    out_dir = Path(os.environ.get("CONCORD_REPORT_DIR", str(work_dir)))
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / "migration_report.json"
    report_file.write_text(json.dumps(report, indent=2))
    logger.info(f"Report: {report_file}")


# ─────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Puppet 7→8 Migration via ADK api_server /run endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Prerequisites:
  Start the ADK api_server first:
    cd adk_migrator
    adk api_server --port 8090

Examples:
  # Full migration against a running ADK server
  python concord_adk_runner.py \\
      --adk-url http://localhost:8090 \\
      --app-name migrator_pattern \\
      --repo-url https://github.com/myorg/puppet-webapp.git \\
      --source-branch main \\
      --push

  # Analysis only (no push)
  python concord_adk_runner.py \\
      --adk-url http://localhost:8090 \\
      --app-name analyzer_pattern \\
      --repo-url https://github.com/myorg/puppet-webapp.git

  # Specific module in a control repo, with SSE streaming
  python concord_adk_runner.py \\
      --adk-url http://adk-service.internal:8090 \\
      --app-name migrator_pattern \\
      --repo-url https://github.com/myorg/puppet-control.git \\
      --module-path modules/webapp \\
      --target-branch puppet8/webapp \\
      --stream \\
      --push
        """,
    )
    parser.add_argument(
        "--adk-url",
        default=os.environ.get("ADK_SERVER_URL", "http://localhost:8090"),
        help="ADK api_server base URL (default: $ADK_SERVER_URL or http://localhost:8090)",
    )
    parser.add_argument(
        "--app-name",
        default="migrator_pattern",
        choices=["analyzer_pattern", "migrator_pattern", "validator_pattern", "coordinator_pattern"],
        help="ADK app/agent name to invoke (default: migrator_pattern)",
    )
    parser.add_argument("--repo-url", required=True, help="GitHub repo clone URL (HTTPS)")
    parser.add_argument("--source-branch", default="main", help="Branch to migrate from")
    parser.add_argument("--target-branch", default=None, help="Target branch (default: auto-generated)")
    parser.add_argument("--module-path", default=".", help="Path to Puppet module within repo")
    parser.add_argument("--stream", action="store_true", help="Use /run_sse for streaming output")
    parser.add_argument("--push", action="store_true", help="Push migrated branch to origin")
    parser.add_argument("--no-push", dest="push", action="store_false")
    parser.add_argument("--timeout", type=int, default=600, help="HTTP timeout in seconds (default: 600)")
    parser.set_defaults(push=False)

    args = parser.parse_args()
    sys.exit(run_pipeline(args))


if __name__ == "__main__":
    main()
