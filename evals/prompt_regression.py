"""Prompt regression evaluation against golden dataset."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from evals.metrics import compute_citation_recall, compute_faithfulness
from universal_copilot.graph.runner import run_case_sync


def evaluate_golden_set() -> Dict[str, Any]:
    golden_file = ROOT / "data" / "golden" / "golden_set.jsonl"
    if not golden_file.exists():
        raise FileNotFoundError(f"Golden set file missing: {golden_file}")

    cases: List[Dict[str, Any]] = []
    with open(golden_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    faithfulness_scores = []
    citation_recall_scores = []
    escalation_accuracy = []

    for c in cases:
        res = run_case_sync(query=c["query"], entity_id=c.get("entity_id"))
        ans = res.final_response

        f_score = compute_faithfulness(ans, c.get("expected_facts", []))
        esc_correct = res.requires_escalation == c.get("should_escalate", False)
        if c.get("should_escalate", False):
            c_score = 1.0 if res.requires_escalation else 0.0
        else:
            c_score = compute_citation_recall(ans, c.get("expected_citation_doc", ""))

        faithfulness_scores.append(f_score)
        citation_recall_scores.append(c_score)
        escalation_accuracy.append(1.0 if esc_correct else 0.0)

    avg_faithfulness = sum(faithfulness_scores) / max(1, len(faithfulness_scores))
    avg_recall = sum(citation_recall_scores) / max(1, len(citation_recall_scores))
    avg_esc = sum(escalation_accuracy) / max(1, len(escalation_accuracy))

    return {
        "total_cases": len(cases),
        "avg_faithfulness": round(avg_faithfulness, 2),
        "avg_citation_recall": round(avg_recall, 2),
        "escalation_accuracy": round(avg_esc, 2),
    }


if __name__ == "__main__":
    report = evaluate_golden_set()
    print("Golden Set Evaluation Report:")
    print(json.dumps(report, indent=2))
