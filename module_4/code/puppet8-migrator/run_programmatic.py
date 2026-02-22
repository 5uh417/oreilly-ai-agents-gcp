#!/usr/bin/env python3
"""
Programmatic ADK Runner for Puppet 7→8 Migration

Demonstrates how to invoke the migration agents programmatically using
Google ADK's InMemoryRunner — no web UI or CLI needed. This is the
pattern you'd use for CI/CD integration or batch processing.

Usage:
    python run_programmatic.py --pattern migrator
    python run_programmatic.py --pattern analyzer
    python run_programmatic.py --pattern validator
    python run_programmatic.py --pattern coordinator --file manifests/init.pp
"""

import argparse
import asyncio
import importlib
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

# Load environment before importing agents
load_dotenv(Path(__file__).parent / "adk_migrator" / ".env")


def read_sample_module() -> dict[str, str]:
    """Read all files from the sample Puppet 7 module."""
    module_dir = Path(__file__).parent / "sample_puppet7_module"
    files = {}
    extensions = {".pp", ".rb", ".yaml", ".yml", ".erb", ".json"}
    for path in module_dir.rglob("*"):
        if path.is_file() and path.suffix in extensions:
            rel = path.relative_to(module_dir)
            files[str(rel)] = path.read_text()
    return files


def format_files(files: dict[str, str]) -> str:
    """Format files into a single string block."""
    parts = []
    for fp, content in sorted(files.items()):
        parts.append(f"--- FILE: {fp} ---\n{content}\n--- END FILE: {fp} ---\n")
    return "\n".join(parts)


async def run_agent(pattern: str, prompt: str):
    """Run the specified pattern agent with the given prompt."""

    # Dynamically import the agent module
    sys.path.insert(0, str(Path(__file__).parent / "adk_migrator"))
    agent_module = importlib.import_module(f"{pattern}_pattern.agent")
    agent = agent_module.root_agent

    print(f"Running agent: {agent.name}")
    print(f"Pattern: {pattern}")
    print(f"Prompt length: {len(prompt)} chars")
    print("-" * 70)

    # Create runner
    runner = InMemoryRunner(agent=agent, app_name="puppet8_migrator")

    # Create a session
    session = await runner.session_service.create_session(
        app_name="puppet8_migrator",
        user_id="migration_user",
    )

    # Build the user message
    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)],
    )

    # Run the agent and collect responses
    print("\nAgent output:")
    print("=" * 70)

    async for event in runner.run_async(
        user_id="migration_user",
        session_id=session.id,
        new_message=user_message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)

    print("=" * 70)
    print("Agent execution complete.")

    # Print session state keys (shows what each agent produced)
    final_session = await runner.session_service.get_session(
        app_name="puppet8_migrator",
        user_id="migration_user",
        session_id=session.id,
    )
    if final_session and final_session.state:
        print("\nSession state keys (agent outputs):")
        for key in final_session.state:
            value = str(final_session.state[key])
            print(f"  {key}: {len(value)} chars")


def main():
    parser = argparse.ArgumentParser(description="Programmatic Puppet 8 Migration Runner")
    parser.add_argument(
        "--pattern",
        choices=["analyzer", "migrator", "validator", "coordinator"],
        required=True,
    )
    parser.add_argument("--file", type=str, default=None)
    args = parser.parse_args()

    files = read_sample_module()

    if args.file:
        if args.file not in files:
            print(f"File not found: {args.file}")
            sys.exit(1)
        file_content = format_files({args.file: files[args.file]})
    else:
        file_content = format_files(files)

    prompts = {
        "analyzer": (
            "Analyze the following Puppet 7 module for ALL Puppet 8 compatibility issues.\n\n"
            + file_content
        ),
        "migrator": (
            "Migrate the following Puppet 7 module to Puppet 8. Apply all changes: "
            "legacy facts, deprecated functions, type annotations, hiera v5, Ruby 3.2.\n\n"
            + file_content
        ),
        "validator": (
            "Validate and fix the following Puppet code for Puppet 8 compatibility.\n\n"
            + file_content
        ),
        "coordinator": (
            "Migrate this Puppet file to Puppet 8.\n\n" + file_content
        ),
    }

    asyncio.run(run_agent(args.pattern, prompts[args.pattern]))


if __name__ == "__main__":
    main()
