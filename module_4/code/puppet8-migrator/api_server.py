#!/usr/bin/env python3
"""
FastAPI server exposing the Puppet 7→8 migration pipeline as REST endpoints.

Concord (or any CI/CD tool) can POST a GitHub repo URL to this API, and it will:
  1. Clone the repo
  2. Run the ADK sequential migration pipeline against all Puppet files
  3. Push the migrated code to a new branch
  4. Return the branch name and a migration summary

Endpoints:
  POST /migrate          — Full migration: clone → migrate → push
  POST /analyze          — Analysis only: clone → analyze → return report
  GET  /health           — Health check
  GET  /status/{job_id}  — Check async job status

Usage:
  pip install -r requirements-api.txt
  uvicorn api_server:app --host 0.0.0.0 --port 8090

Environment Variables:
  GOOGLE_API_KEY          — Required. Google AI Studio API key.
  GOOGLE_GENAI_USE_VERTEXAI — Set to "0" for AI Studio, "1" for Vertex AI.
  GIT_TOKEN               — Optional. GitHub PAT for private repos (used in clone URL).
  GIT_AUTHOR_NAME         — Optional. Git commit author name. Default: "puppet8-migrator".
  GIT_AUTHOR_EMAIL        — Optional. Git commit author email. Default: "puppet8-migrator@noreply".
"""

import asyncio
import importlib
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# Ensure adk_migrator is importable
sys.path.insert(0, str(Path(__file__).parent / "adk_migrator"))

load_dotenv(Path(__file__).parent / "adk_migrator" / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("puppet8-migrator-api")

# ─────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────

class MigrationRequest(BaseModel):
    """Request body for the /migrate and /analyze endpoints."""
    repo_url: str = Field(
        ...,
        description="GitHub clone URL (HTTPS). Example: https://github.com/myorg/puppet-webapp.git",
    )
    source_branch: str = Field(
        default="main",
        description="Branch to migrate from. Default: main",
    )
    target_branch: str | None = Field(
        default=None,
        description=(
            "Branch name for migrated code. Default: auto-generated as "
            "'puppet8-migration/<source_branch>/<timestamp>'"
        ),
    )
    module_path: str = Field(
        default=".",
        description=(
            "Relative path within the repo to the Puppet module root. "
            "Use '.' if the repo root IS the module. Example: 'modules/webapp'"
        ),
    )
    pattern: str = Field(
        default="migrator",
        description="ADK pattern to use: 'migrator' (full pipeline), 'analyzer' (report only), 'validator' (iterative fix).",
    )
    commit_message: str | None = Field(
        default=None,
        description="Custom commit message. Default: auto-generated.",
    )
    push_results: bool = Field(
        default=True,
        description="Whether to push the migrated branch to origin. Set False for dry-run.",
    )


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MigrationJob(BaseModel):
    job_id: str
    status: JobStatus
    created_at: str
    completed_at: str | None = None
    request: MigrationRequest
    result: dict[str, Any] | None = None
    error: str | None = None


# ─────────────────────────────────────────────────────────────────────
# In-memory job store (use Redis/DB in production)
# ─────────────────────────────────────────────────────────────────────
jobs: dict[str, MigrationJob] = {}

# ─────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Puppet 7→8 Migration API",
    description="ADK-powered multi-agent pipeline for migrating Puppet 7 modules to Puppet 8.",
    version="1.0.0",
)


@app.get("/health")
async def health():
    """Health check endpoint for Concord/load balancer probes."""
    api_key_set = bool(os.environ.get("GOOGLE_API_KEY"))
    return {
        "status": "healthy",
        "google_api_key_configured": api_key_set,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/migrate", response_model=MigrationJob)
async def migrate(request: MigrationRequest, background_tasks: BackgroundTasks):
    """
    Trigger a full Puppet 7→8 migration.

    This is an async endpoint — it returns a job_id immediately and
    runs the migration in the background. Poll GET /status/{job_id}
    to check progress.
    """
    job_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()

    job = MigrationJob(
        job_id=job_id,
        status=JobStatus.PENDING,
        created_at=now,
        request=request,
    )
    jobs[job_id] = job

    background_tasks.add_task(run_migration_job, job_id)

    return job


@app.post("/analyze", response_model=MigrationJob)
async def analyze(request: MigrationRequest, background_tasks: BackgroundTasks):
    """
    Run analysis only (no code changes, no push).
    Returns a compatibility report.
    """
    request.push_results = False
    request.pattern = "analyzer"

    job_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()

    job = MigrationJob(
        job_id=job_id,
        status=JobStatus.PENDING,
        created_at=now,
        request=request,
    )
    jobs[job_id] = job

    background_tasks.add_task(run_migration_job, job_id)

    return job


@app.get("/status/{job_id}", response_model=MigrationJob)
async def get_status(job_id: str):
    """Check status of a migration job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return jobs[job_id]


# ─────────────────────────────────────────────────────────────────────
# Core Migration Logic
# ─────────────────────────────────────────────────────────────────────

def inject_git_token(url: str) -> str:
    """Inject GIT_TOKEN into HTTPS clone URL for private repos."""
    token = os.environ.get("GIT_TOKEN")
    if token and url.startswith("https://"):
        # https://github.com/... → https://<token>@github.com/...
        return url.replace("https://", f"https://{token}@", 1)
    return url


def clone_repo(repo_url: str, branch: str, work_dir: Path) -> Path:
    """Clone the repo into work_dir and checkout the specified branch."""
    clone_url = inject_git_token(repo_url)
    repo_dir = work_dir / "repo"

    logger.info(f"Cloning {repo_url} (branch: {branch}) into {repo_dir}")

    subprocess.run(
        ["git", "clone", "--branch", branch, "--single-branch", "--depth", "50", clone_url, str(repo_dir)],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )

    return repo_dir


def collect_puppet_files(module_root: Path) -> dict[str, str]:
    """Collect all Puppet-relevant files from the module directory."""
    files = {}
    extensions = {".pp", ".rb", ".yaml", ".yml", ".erb", ".epp", ".json"}
    skip_dirs = {".git", ".vagrant", "vendor", "pkg", ".bundle", "spec/fixtures"}

    for path in module_root.rglob("*"):
        # Skip irrelevant directories
        rel = path.relative_to(module_root)
        if any(part in skip_dirs for part in rel.parts):
            continue

        if path.is_file() and path.suffix in extensions:
            files[str(rel)] = path.read_text(errors="replace")

    return files


def format_files_for_prompt(files: dict[str, str]) -> str:
    """Format collected files into the prompt format the agents expect."""
    parts = []
    for filepath, content in sorted(files.items()):
        parts.append(f"--- FILE: {filepath} ---")
        parts.append(content)
        parts.append(f"--- END FILE: {filepath} ---\n")
    return "\n".join(parts)


def build_prompt(pattern: str, file_content: str) -> str:
    """Build the appropriate prompt for the selected agent pattern."""
    prompts = {
        "analyzer": (
            "Analyze the following Puppet 7 module for ALL Puppet 8 compatibility issues. "
            "Check manifests, Ruby code, Hiera config, and templates. "
            "Produce a detailed report for each file.\n\n"
            + file_content
        ),
        "migrator": (
            "Migrate the following Puppet 7 module to be fully Puppet 8 compatible. "
            "Apply all necessary changes: legacy facts → structured facts, "
            "deprecated functions → modern replacements, add type annotations, "
            "convert hiera v3 → v5, fix Ruby 3.2 compatibility. "
            "Output the complete migrated files.\n\n"
            + file_content
        ),
        "validator": (
            "Validate and iteratively fix the following Puppet code until it passes "
            "all Puppet 8 compatibility checks.\n\n"
            + file_content
        ),
    }
    return prompts.get(pattern, prompts["migrator"])


async def run_adk_agent(pattern: str, prompt: str) -> dict[str, str]:
    """
    Run the specified ADK agent pattern and return session state.

    Returns a dict of output_key → value for all agent outputs.
    """
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    agent_module = importlib.import_module(f"{pattern}_pattern.agent")
    agent = agent_module.root_agent

    runner = InMemoryRunner(agent=agent, app_name="puppet8_migrator_api")
    user_id = f"concord_{uuid.uuid4().hex[:8]}"

    session = await runner.session_service.create_session(
        app_name="puppet8_migrator_api",
        user_id=user_id,
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)],
    )

    # Collect all text output from the agent
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

    # Get final session state
    final_session = await runner.session_service.get_session(
        app_name="puppet8_migrator_api",
        user_id=user_id,
        session_id=session.id,
    )

    result = {
        "agent_output": "\n".join(full_output),
    }

    if final_session and final_session.state:
        for key, value in final_session.state.items():
            result[key] = str(value)

    return result


def extract_migrated_files(agent_output: str) -> dict[str, str]:
    """
    Parse the agent's output to extract individual migrated files.

    The migration agent outputs files in the format:
    --- BEGIN FILE: <path> ---
    <content>
    --- END FILE: <path> ---
    """
    files = {}
    current_file = None
    current_lines = []

    for line in agent_output.split("\n"):
        if line.startswith("--- BEGIN FILE:") or line.startswith("--- FILE:"):
            # Extract filename
            parts = line.split(":", 1)
            if len(parts) > 1:
                fname = parts[1].strip().rstrip(" -").strip()
                current_file = fname
                current_lines = []
        elif line.startswith("--- END FILE:") or line.startswith("--- END"):
            if current_file and current_lines:
                files[current_file] = "\n".join(current_lines)
            current_file = None
            current_lines = []
        elif current_file is not None:
            current_lines.append(line)

    # Handle case where last file isn't terminated
    if current_file and current_lines:
        files[current_file] = "\n".join(current_lines)

    return files


def write_migrated_files(repo_dir: Path, module_path: str, migrated_files: dict[str, str]):
    """Write migrated file contents back to the cloned repo."""
    module_root = repo_dir / module_path if module_path != "." else repo_dir

    for rel_path, content in migrated_files.items():
        target = module_root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        logger.info(f"  Wrote: {rel_path}")


def create_branch_and_push(
    repo_dir: Path,
    target_branch: str,
    commit_message: str,
    push: bool,
) -> dict[str, Any]:
    """Create a new branch, commit changes, and optionally push."""
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = os.environ.get("GIT_AUTHOR_NAME", "puppet8-migrator")
    env["GIT_AUTHOR_EMAIL"] = os.environ.get("GIT_AUTHOR_EMAIL", "puppet8-migrator@noreply")
    env["GIT_COMMITTER_NAME"] = env["GIT_AUTHOR_NAME"]
    env["GIT_COMMITTER_EMAIL"] = env["GIT_AUTHOR_EMAIL"]

    def git(*args):
        result = subprocess.run(
            ["git", "-C", str(repo_dir)] + list(args),
            capture_output=True, text=True, timeout=60, env=env,
        )
        if result.returncode != 0:
            logger.error(f"git {' '.join(args)} failed: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, "git", result.stderr)
        return result.stdout.strip()

    # Create and checkout the target branch
    git("checkout", "-b", target_branch)

    # Stage all changes
    git("add", "-A")

    # Check if there are changes to commit
    status = git("status", "--porcelain")
    if not status:
        return {
            "branch": target_branch,
            "pushed": False,
            "changes": 0,
            "message": "No changes detected — module may already be Puppet 8 compatible.",
        }

    change_count = len(status.strip().split("\n"))

    # Commit
    git("commit", "-m", commit_message)

    commit_hash = git("rev-parse", "HEAD")

    result = {
        "branch": target_branch,
        "commit": commit_hash,
        "changes": change_count,
        "message": commit_message,
        "pushed": False,
    }

    if push:
        git("push", "-u", "origin", target_branch)
        result["pushed"] = True
        logger.info(f"Pushed branch '{target_branch}' to origin")

    return result


# ─────────────────────────────────────────────────────────────────────
# Background Job Runner
# ─────────────────────────────────────────────────────────────────────

async def run_migration_job(job_id: str):
    """Execute the full migration pipeline as a background task."""
    job = jobs[job_id]
    job.status = JobStatus.RUNNING
    req = job.request

    work_dir = Path(tempfile.mkdtemp(prefix=f"puppet8-{job_id}-"))

    try:
        logger.info(f"[{job_id}] Starting migration: {req.repo_url} ({req.source_branch})")

        # 1. Clone
        repo_dir = clone_repo(req.repo_url, req.source_branch, work_dir)
        logger.info(f"[{job_id}] Clone complete")

        # 2. Collect files
        module_root = repo_dir / req.module_path if req.module_path != "." else repo_dir
        if not module_root.exists():
            raise FileNotFoundError(
                f"Module path '{req.module_path}' not found in repo. "
                f"Available directories: {[d.name for d in repo_dir.iterdir() if d.is_dir() and d.name != '.git']}"
            )

        puppet_files = collect_puppet_files(module_root)
        logger.info(f"[{job_id}] Collected {len(puppet_files)} files")

        if not puppet_files:
            raise ValueError(
                f"No Puppet files (.pp, .rb, .yaml, .erb) found in '{req.module_path}'. "
                "Verify the module_path parameter."
            )

        # 3. Build prompt and run agent
        file_content = format_files_for_prompt(puppet_files)
        prompt = build_prompt(req.pattern, file_content)
        logger.info(f"[{job_id}] Running ADK agent: {req.pattern} (prompt: {len(prompt)} chars)")

        agent_result = await run_adk_agent(req.pattern, prompt)
        logger.info(f"[{job_id}] Agent complete. Output keys: {list(agent_result.keys())}")

        # 4. For migration patterns, extract files and commit
        git_result = None

        if req.pattern in ("migrator", "validator"):
            # Try to extract files from the final output
            output_text = agent_result.get("final_output") or agent_result.get("current_code") or agent_result.get("agent_output", "")
            migrated_files = extract_migrated_files(output_text)

            if migrated_files:
                logger.info(f"[{job_id}] Extracted {len(migrated_files)} migrated files")
                write_migrated_files(repo_dir, req.module_path, migrated_files)

                # Generate target branch name
                target_branch = req.target_branch or (
                    f"puppet8-migration/{req.source_branch}/"
                    f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
                )

                commit_msg = req.commit_message or (
                    f"Migrate Puppet 7 → 8: {req.module_path}\n\n"
                    f"Automated migration by puppet8-migrator ADK pipeline.\n"
                    f"Pattern: {req.pattern}\n"
                    f"Files migrated: {len(migrated_files)}\n"
                    f"Source branch: {req.source_branch}\n"
                    f"Job ID: {job_id}"
                )

                git_result = create_branch_and_push(
                    repo_dir, target_branch, commit_msg, req.push_results,
                )
                logger.info(f"[{job_id}] Git result: {git_result}")
            else:
                logger.warning(f"[{job_id}] Could not extract migrated files from agent output")

        # 5. Build result
        job.result = {
            "files_analyzed": len(puppet_files),
            "file_list": sorted(puppet_files.keys()),
            "pattern_used": req.pattern,
            "agent_output_keys": list(agent_result.keys()),
            "git": git_result,
        }

        # Include analysis/migration summaries (truncated for API response)
        for key in ("migration_manifest", "review_report", "manifest_analysis",
                     "ruby_analysis", "hiera_analysis", "template_analysis",
                     "validation_report", "final_output", "current_code"):
            if key in agent_result:
                value = agent_result[key]
                job.result[key] = value[:5000] + "..." if len(value) > 5000 else value

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"[{job_id}] Migration completed successfully")

    except Exception as e:
        logger.exception(f"[{job_id}] Migration failed")
        job.status = JobStatus.FAILED
        job.error = f"{type(e).__name__}: {str(e)}"
        job.completed_at = datetime.now(timezone.utc).isoformat()

    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────
# Synchronous endpoint for simpler Concord integration
# ─────────────────────────────────────────────────────────────────────

@app.post("/migrate/sync")
async def migrate_sync(request: MigrationRequest):
    """
    Synchronous migration — blocks until complete.

    Use this if Concord is calling via curl and waiting for the response.
    For long-running migrations, prefer the async /migrate endpoint.

    WARNING: This can take several minutes depending on module size.
    Set appropriate timeout in your Concord task (recommend 600s).
    """
    job_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()

    job = MigrationJob(
        job_id=job_id,
        status=JobStatus.PENDING,
        created_at=now,
        request=request,
    )
    jobs[job_id] = job

    # Run synchronously (await the coroutine directly)
    await run_migration_job(job_id)

    return jobs[job_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
