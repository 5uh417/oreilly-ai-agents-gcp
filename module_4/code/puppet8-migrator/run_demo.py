#!/usr/bin/env python3
"""
Puppet 7→8 Migration Demo Runner

Reads the sample Puppet 7 module and feeds it into the ADK migration agents.
This script demonstrates how to programmatically invoke the agents without
the ADK web UI, useful for CI/CD integration.

Usage:
    python run_demo.py --pattern <analyzer|migrator|validator|coordinator>
    python run_demo.py --pattern migrator --file manifests/init.pp
"""

import argparse
import os
import sys
from pathlib import Path


def read_sample_module() -> dict[str, str]:
    """Read all files from the sample Puppet 7 module into a dict."""
    module_dir = Path(__file__).parent / "sample_puppet7_module"
    files = {}

    extensions = {".pp", ".rb", ".yaml", ".yml", ".erb", ".json"}

    for path in module_dir.rglob("*"):
        if path.is_file() and path.suffix in extensions:
            rel_path = path.relative_to(module_dir)
            files[str(rel_path)] = path.read_text()

    return files


def format_files_for_prompt(files: dict[str, str], filter_ext: str | None = None) -> str:
    """Format file contents into a single prompt string."""
    parts = []
    for filepath, content in sorted(files.items()):
        if filter_ext and not filepath.endswith(filter_ext):
            continue
        parts.append(f"--- FILE: {filepath} ---")
        parts.append(content)
        parts.append(f"--- END FILE: {filepath} ---\n")
    return "\n".join(parts)


def print_banner(pattern: str):
    """Print a nice banner for the demo."""
    banners = {
        "analyzer": "PARALLEL ANALYZER — Concurrent Puppet 8 Compatibility Analysis",
        "migrator": "SEQUENTIAL PIPELINE — Analyze → Migrate → Review → Finalize",
        "validator": "LOOP VALIDATOR — Iterative Validation & Fix Cycle",
        "coordinator": "COORDINATOR-DISPATCHER — File Type Routing",
    }
    title = banners.get(pattern, pattern)
    width = max(len(title) + 4, 70)
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width + "\n")


def main():
    parser = argparse.ArgumentParser(description="Puppet 7→8 Migration Demo")
    parser.add_argument(
        "--pattern",
        choices=["analyzer", "migrator", "validator", "coordinator"],
        required=False,
        default=None,
        help="Which ADK pattern to demonstrate",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Specific file from sample module to process (e.g., manifests/init.pp)",
    )
    parser.add_argument(
        "--list-files",
        action="store_true",
        help="List all files in the sample module and exit",
    )
    args = parser.parse_args()

    files = read_sample_module()

    if args.list_files:
        print("Files in sample Puppet 7 module:")
        for filepath in sorted(files.keys()):
            print(f"  {filepath}")
        return

    if not args.pattern:
        parser.error("--pattern is required unless --list-files is used")

    print_banner(args.pattern)

    if args.file:
        if args.file in files:
            prompt_content = format_files_for_prompt({args.file: files[args.file]})
        else:
            print(f"Error: File '{args.file}' not found in sample module.")
            print("Available files:")
            for f in sorted(files.keys()):
                print(f"  {f}")
            sys.exit(1)
    else:
        prompt_content = format_files_for_prompt(files)

    print("Sample module files loaded:")
    for f in sorted(files.keys()):
        marker = " <<<" if (args.file and f == args.file) else ""
        print(f"  {f}{marker}")
    print()

    # Build the prompt based on pattern
    prompts = {
        "analyzer": (
            "Analyze the following Puppet 7 module for ALL Puppet 8 compatibility issues. "
            "Check manifests, Ruby code, Hiera config, and templates.\n\n"
            + prompt_content
        ),
        "migrator": (
            "Migrate the following Puppet 7 module to be fully Puppet 8 compatible. "
            "Apply all necessary changes: legacy facts, deprecated functions, type annotations, "
            "hiera v5, Ruby 3.2 compatibility.\n\n"
            + prompt_content
        ),
        "validator": (
            "Validate and iteratively fix the following Puppet code until it passes "
            "all Puppet 8 compatibility checks.\n\n"
            + prompt_content
        ),
        "coordinator": (
            "I have a Puppet file that needs migration to Puppet 8. "
            "Please route it to the right specialist.\n\n"
            + prompt_content
        ),
    }

    prompt = prompts[args.pattern]

    print(f"Prompt length: {len(prompt)} characters")
    print(f"Pattern: {args.pattern}")
    print()
    print("To run this with ADK, use one of these methods:")
    print()
    print("  Method 1 — ADK Web UI:")
    print("    cd adk_migrator")
    print("    adk web")
    print(f"    Then select '{args.pattern}_pattern' from the dropdown")
    print(f"    Paste the prompt above into the chat")
    print()
    print("  Method 2 — ADK CLI:")
    print(f"    cd adk_migrator")
    print(f"    adk run {args.pattern}_pattern")
    print(f"    Then paste the sample module content")
    print()
    print("  Method 3 — Programmatic (requires google-adk runner):")
    print("    See the InMemoryRunner example in run_programmatic.py")
    print()
    print("-" * 70)
    print("GENERATED PROMPT (first 500 chars):")
    print("-" * 70)
    print(prompt[:500])
    if len(prompt) > 500:
        print(f"\n... ({len(prompt) - 500} more characters)")


if __name__ == "__main__":
    main()
