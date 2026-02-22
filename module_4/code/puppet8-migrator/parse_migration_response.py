#!/usr/bin/env python3
"""
Standalone utility: parse the raw JSON response from adk api_server /run
and write migrated files back to a directory on disk.

This is extracted as its own script so it can be used independently of
concord_adk_runner.py — useful for:

  1. Debugging: inspect what the ADK server returned without re-running
     the full pipeline
  2. Shell script integration: pipe curl output directly into this script
  3. Re-running the file-write step when the ADK call succeeded but a
     subsequent git step failed

Usage:

  # Parse a saved ADK response and write files into /tmp/repo
  python parse_migration_response.py \
      --response-file /tmp/adk_response.json \
      --output-dir /tmp/repo \
      --module-path modules/webapp

  # Pipe curl output directly (useful in shell scripts)
  curl -s -X POST http://localhost:8090/run \
      -H "Content-Type: application/json" \
      -d @payload.json \
    | python parse_migration_response.py --output-dir /tmp/repo

  # Show what files the response contains without writing them
  python parse_migration_response.py \
      --response-file /tmp/adk_response.json \
      --dry-run

  # Extract a single specific file
  python parse_migration_response.py \
      --response-file /tmp/adk_response.json \
      --output-dir /tmp/repo \
      --only manifests/init.pp

ADK /run response structure (for reference):

  The /run endpoint returns a JSON array of events. Each event can contain:

  {
    "content": {
      "role": "model",
      "parts": [
        { "text": "... migrated file output ..." }
      ]
    },
    "author": "MigrationFinalizer",
    "actions": {
      "stateDelta": {
        "final_output": "--- BEGIN FILE: manifests/init.pp ---\\n...",
        "migrated_code": "...",
        "current_code":  "...",
        "migration_manifest": "...",
        "review_report": "..."
      }
    }
  }

  Migrated file content lives in one of three places (tried in order):
    1. stateDelta["final_output"]    — Finalizer agent output (most complete)
    2. stateDelta["migrated_code"]   — CodeMigrator output
    3. stateDelta["current_code"]    — Validator loop final state
    4. All content.parts[*].text joined — fallback full-text scan
"""

import argparse
import json
import sys
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────
# Event parsing
# ─────────────────────────────────────────────────────────────────────

def load_response(response_file: Path | None) -> list[dict]:
    """Load the ADK /run response from a file or stdin."""
    if response_file:
        raw = response_file.read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()

    data = json.loads(raw)

    # /run returns a list of events; /run_sse may return individual objects
    if isinstance(data, list):
        return data
    return [data]


def extract_state_delta(events: list[dict]) -> dict[str, str]:
    """
    Collect all stateDelta fields across all events and merge them.

    Later events overwrite earlier ones for the same key, which is correct
    because the Finalizer runs last and produces the most complete output.
    """
    merged: dict[str, str] = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        actions = event.get("actions", {})
        if not isinstance(actions, dict):
            continue
        state_delta = actions.get("stateDelta", {})
        if isinstance(state_delta, dict):
            for key, value in state_delta.items():
                if value:  # don't overwrite a good value with an empty one
                    merged[key] = str(value)
    return merged


def extract_full_text(events: list[dict]) -> str:
    """
    Extract all text from content.parts across all events.
    Used as a fallback when stateDelta doesn't contain file markers.
    """
    parts: list[str] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        content = event.get("content", {})
        if not isinstance(content, dict):
            continue
        for part in content.get("parts", []):
            if isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────
# File block parser
# ─────────────────────────────────────────────────────────────────────

def parse_file_blocks(text: str) -> dict[str, str]:
    """
    Parse all --- BEGIN FILE / --- FILE / --- END FILE blocks from text.

    Supports both marker formats the agents may emit:
      --- BEGIN FILE: path/to/file.pp ---
      --- FILE: path/to/file.pp ---
    and closing:
      --- END FILE: path/to/file.pp ---
      --- END FILE ---
      --- END ---
    """
    files: dict[str, str] = {}
    current_file: str | None = None
    current_lines: list[str] = []

    for line in text.split("\n"):
        stripped = line.strip()

        # Detect opening marker
        if stripped.startswith("--- BEGIN FILE:") or stripped.startswith("--- FILE:"):
            # If we were already collecting a file, save it (handles missing END marker)
            if current_file and current_lines:
                files[current_file] = "\n".join(current_lines).strip()

            # Extract the filename portion
            colon_pos = stripped.index(":")
            raw_name = stripped[colon_pos + 1:].strip().rstrip("-").strip()
            current_file = raw_name
            current_lines = []
            continue

        # Detect closing marker
        if stripped.startswith("--- END FILE") or stripped == "--- END ---":
            if current_file and current_lines:
                files[current_file] = "\n".join(current_lines).strip()
            current_file = None
            current_lines = []
            continue

        # Accumulate content lines
        if current_file is not None:
            current_lines.append(line)

    # Handle unterminated final block
    if current_file and current_lines:
        files[current_file] = "\n".join(current_lines).strip()

    return files


def find_best_source(state: dict[str, str], full_text: str) -> tuple[str, str]:
    """
    Return (source_label, text_to_parse) using priority order:
      1. final_output  — Finalizer agent; most complete and reviewed
      2. migrated_code — CodeMigrator agent; reviewed but not finalized
      3. current_code  — Validator loop; last iteration's output
      4. full_text     — entire content.parts concatenation; last resort
    """
    for key in ("final_output", "migrated_code", "current_code"):
        value = state.get(key, "")
        if value and ("--- FILE:" in value or "--- BEGIN FILE:" in value):
            return key, value

    # Fall back to scanning all text
    if "--- FILE:" in full_text or "--- BEGIN FILE:" in full_text:
        return "full_text_scan", full_text

    return "none", ""


# ─────────────────────────────────────────────────────────────────────
# File writer
# ─────────────────────────────────────────────────────────────────────

def write_files(
    files: dict[str, str],
    output_dir: Path,
    module_path: str,
    only: str | None,
    dry_run: bool,
) -> int:
    """Write migrated files to output_dir. Returns count of files written."""
    root = output_dir / module_path if module_path != "." else output_dir
    written = 0

    for rel_path, content in sorted(files.items()):
        if only and rel_path != only:
            continue

        if dry_run:
            print(f"  [dry-run] would write: {rel_path}  ({len(content)} bytes)")
            written += 1
            continue

        target = root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"  wrote: {rel_path}  ({len(content)} bytes)")
        written += 1

    return written


# ─────────────────────────────────────────────────────────────────────
# Event summary printer
# ─────────────────────────────────────────────────────────────────────

def summarise_events(events: list[dict]):
    """Print a human-readable summary of the events for debugging."""
    print(f"\nTotal events in response: {len(events)}")
    for i, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        author = event.get("author", "unknown")
        content = event.get("content", {})
        parts = content.get("parts", []) if isinstance(content, dict) else []
        text_len = sum(len(p.get("text", "")) for p in parts if isinstance(p, dict))
        actions = event.get("actions", {})
        state_keys = list(actions.get("stateDelta", {}).keys()) if isinstance(actions, dict) else []
        print(f"  [{i:02d}] author={author:<25}  text={text_len:>6} chars  stateDelta={state_keys}")


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Parse ADK api_server /run response and write migrated files to disk.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse a saved response
  python parse_migration_response.py \\
      --response-file /tmp/adk_response.json \\
      --output-dir /tmp/repo

  # Pipe from curl
  curl -s -X POST http://localhost:8090/run -H "Content-Type: application/json" \\
      -d @payload.json | python parse_migration_response.py --output-dir /tmp/repo

  # Dry-run: just show what would be written
  python parse_migration_response.py \\
      --response-file /tmp/adk_response.json \\
      --dry-run

  # Summarise events to understand the response structure
  python parse_migration_response.py \\
      --response-file /tmp/adk_response.json \\
      --summarise-only

  # Extract one specific file
  python parse_migration_response.py \\
      --response-file /tmp/adk_response.json \\
      --output-dir /tmp/repo \\
      --only manifests/init.pp
        """,
    )
    parser.add_argument(
        "--response-file",
        type=Path,
        default=None,
        help="Path to saved ADK /run JSON response. Reads from stdin if omitted.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to write migrated files into. Required unless --dry-run or --summarise-only.",
    )
    parser.add_argument(
        "--module-path",
        default=".",
        help="Subdirectory within --output-dir to write files (default: .).",
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Extract only this one file path (relative to module root).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and list files that would be written, without touching disk.",
    )
    parser.add_argument(
        "--summarise-only",
        action="store_true",
        help="Print a summary of events in the response and exit.",
    )
    parser.add_argument(
        "--dump-state",
        action="store_true",
        help="Print all stateDelta keys and their lengths, then exit.",
    )
    parser.add_argument(
        "--show-source",
        action="store_true",
        help="Print which state key was used as the source for file extraction.",
    )
    args = parser.parse_args()

    # ── Load ──
    try:
        events = load_response(args.response_file)
    except json.JSONDecodeError as e:
        print(f"Error: response is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # ── Summarise mode ──
    if args.summarise_only:
        summarise_events(events)
        return

    # ── Extract state ──
    state = extract_state_delta(events)
    full_text = extract_full_text(events)

    if args.dump_state:
        print(f"\nstateDelta keys found across all events:")
        if not state:
            print("  (none)")
        else:
            for key, value in sorted(state.items()):
                file_count = value.count("--- FILE:") + value.count("--- BEGIN FILE:")
                print(f"  {key:<30} {len(value):>8} chars  {file_count} file blocks")
        return

    # ── Find best text source ──
    source_label, source_text = find_best_source(state, full_text)

    if args.show_source or not source_text:
        print(f"Source used for file extraction: {source_label}")
        if not source_text:
            summarise_events(events)

    if not source_text:
        print(
            "\nNo file blocks found in response.\n"
            "Use --summarise-only and --dump-state to inspect what the ADK server returned.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Parse file blocks ──
    files = parse_file_blocks(source_text)

    if not files:
        print(
            f"Parsed {len(source_text)} chars from '{source_label}' but found no file blocks.\n"
            "The agent may not have emitted --- FILE: --- markers. "
            "Use --dump-state to check available state keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"\nFound {len(files)} migrated file(s) in '{source_label}':")
    for rel_path in sorted(files):
        print(f"  {rel_path}  ({len(files[rel_path])} bytes)")

    # ── Write mode ──
    if not args.dry_run and not args.output_dir:
        print(
            "\nNo --output-dir specified. Use --dry-run to preview or "
            "--output-dir <path> to write files.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.output_dir or args.dry_run:
        out_dir = args.output_dir or Path("/dev/null")
        print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Writing to: {out_dir}/{args.module_path}")
        written = write_files(files, out_dir, args.module_path, args.only, args.dry_run)
        print(f"\n{'Would write' if args.dry_run else 'Wrote'} {written} file(s).")


if __name__ == "__main__":
    main()
