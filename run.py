#!/usr/bin/env python3
"""Unified CLI entrypoint for Universal Document & Case Resolution Copilot.

Usage:
    python run.py demo          # Run deterministic sample cases across domains
    python run.py ask "..."     # Query the copilot for a single case resolution
    python run.py web           # Launch interactive Streamlit Web UI
    python run.py serve-mcp     # Start the FastMCP tool server
    python run.py eval          # Run golden set benchmarks and regression checks
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def ensure_synthetic_data() -> None:
    data_dir = ROOT / "data" / "synthetic"
    if not (data_dir / "cases.json").exists():
        print("Generating required synthetic corpus and sample documents...")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_synthetic_data.py")], cwd=ROOT, check=True)


def main() -> int:
    args = sys.argv[1:] or ["demo"]
    cmd = args[0].lower()
    ensure_synthetic_data()

    if cmd == "demo":
        from universal_copilot.graph.runner import run_case_sync
        sample_cases = [
            ("CASE-DEMO-01", "What is our expense submission window, and can a 75-day-old claim be reimbursed?", "ENT-1001"),
            ("CASE-DEMO-02", "Our database uptime dropped to 98.6%. What service credit are we owed under MSA-2024-8891?", "ENT-1002"),
            ("CASE-DEMO-03", "I was threatened with termination after reporting safety violations. This is unlawful retaliation.", "ENT-1001"),
        ]

        print("\n" + "=" * 70)
        print("[RUNNING UNIVERSAL DOCUMENT & CASE RESOLUTION COPILOT DEMO]")
        print("=" * 70)

        for cid, query, ent in sample_cases:
            print(f"\n>> Case: {cid} | Entity: {ent}")
            print(f"  Query: \"{query}\"")
            res = run_case_sync(query=query, case_id=cid, entity_id=ent)
            print(f"  Execution Route: {' -> '.join(res.visited_nodes)}")
            print(f"  Latency: {res.duration_ms:.1f}ms | Grounded: {res.is_grounded} | Escalated: {res.requires_escalation}")
            print("  --- Response ---")
            for line in res.final_response.splitlines()[:10]:
                print(f"  {line}")
            if res.citations:
                print("  --- Citations ---")
                for c in res.citations:
                    print(f"  * {c.format_bracket()}: {c.quote[:80]}...")
            print("-" * 70)

        print("\n[SUCCESS] Demo finished successfully!\n")
        return 0

    if cmd == "ask":
        from universal_copilot.cli import main as cli_main
        return cli_main(["ask"] + args[1:])

    if cmd == "web":
        ui_script = ROOT / "src" / "universal_copilot" / "ui" / "streamlit_app.py"
        return subprocess.run([sys.executable, "-m", "streamlit", "run", str(ui_script)], cwd=ROOT).returncode

    if cmd == "serve-mcp":
        transport = args[1] if len(args) > 1 else "stdio"
        from universal_copilot.mcp.server import start_server
        start_server(transport=transport)
        return 0

    if cmd == "eval":
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "run_benchmarks.py")], cwd=ROOT).returncode

    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
