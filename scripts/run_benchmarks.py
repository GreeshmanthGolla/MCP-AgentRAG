#!/usr/bin/env python3
"""Run golden set benchmarks and measure accuracy, citation recall, and latency."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from evals.prompt_regression import evaluate_golden_set

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    print("=" * 60)
    print("[BENCHMARK HARNESS: UNIVERSAL DOCUMENT COPILOT]")
    print("=" * 60)

    t0 = time.perf_counter()
    report = evaluate_golden_set()
    elapsed = time.perf_counter() - t0

    print(f"\nCompleted evaluation of {report['total_cases']} golden test cases in {elapsed:.2f}s:")
    print("-" * 60)
    print(f"  * Average Faithfulness   : {report['avg_faithfulness'] * 100:.1f}% (target >= 85%)")
    print(f"  * Citation Recall        : {report['avg_citation_recall'] * 100:.1f}% (target >= 90%)")
    print(f"  * Escalation Precision   : {report['escalation_accuracy'] * 100:.1f}% (target = 100%)")
    print("-" * 60)

    # Load baseline
    baseline_path = ROOT / "evals" / "baselines" / "quality_baseline.json"
    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        passed = (
            report["avg_faithfulness"] >= baseline["min_faithfulness"]
            and report["avg_citation_recall"] >= baseline["min_citation_recall"]
        )
        status = "PASSED (Meets Quality Baseline)" if passed else "FAILED"
        print(f"Regression Check Status: {status}")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
