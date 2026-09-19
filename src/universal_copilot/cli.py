"""Interactive CLI handler for Universal Copilot commands."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from universal_copilot.graph.runner import run_case_sync


def main(args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="universal-copilot",
        description="Universal Document & Case Resolution Copilot CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Ask subcommand
    ask_parser = subparsers.add_parser("ask", help="Query the copilot for a case resolution")
    ask_parser.add_argument("query", help="The natural language inquiry or case question")
    ask_parser.add_argument("--entity", "-e", default=None, help="Optional Entity ID (e.g. ENT-1001)")
    ask_parser.add_argument("--doc", "-d", action="append", default=[], help="Specific document name to query")
    ask_parser.add_argument("--case-id", default=None, help="Optional Case ID")

    parsed = parser.parse_args(args)

    if parsed.command == "ask":
        print(f"\n[Case Resolution Copilot] Processing query: '{parsed.query}'...")
        if parsed.entity:
            print(f"Entity: {parsed.entity}")

        result = run_case_sync(
            query=parsed.query,
            case_id=parsed.case_id,
            entity_id=parsed.entity,
            target_docs=parsed.doc or None,
        )

        print("\n" + "=" * 60)
        print(f"Case ID: {result.case_id}")
        print(f"Latency: {result.duration_ms:.1f}ms | Grounded: {result.is_grounded} | Escalated: {result.requires_escalation}")
        print(f"Execution Route: {' -> '.join(result.visited_nodes)}")
        print("=" * 60)
        print("\n" + result.final_response + "\n")
        print("=" * 60)
        if result.citations:
            print("Citations Found:")
            for c in result.citations:
                print(f"  * {c.format_bracket()}: {c.quote[:90]}...")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
