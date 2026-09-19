"""Evaluation metrics: Faithfulness, Citation Recall, and Hallucination Scores."""
from __future__ import annotations

import re
from typing import List, Set


def compute_faithfulness(answer: str, ground_truth_facts: List[str]) -> float:
    """Computes fraction of ground truth facts covered in the synthesized answer."""
    if not ground_truth_facts:
        return 1.0
    covered = 0
    ans_lower = answer.lower()
    for fact in ground_truth_facts:
        # Check significant keywords
        words = [w for w in re.findall(r"\w+", fact.lower()) if len(w) > 3]
        if words and any(w in ans_lower for w in words):
            covered += 1

    return round(covered / len(ground_truth_facts), 2)


def compute_citation_recall(answer: str, expected_doc: str) -> float:
    """Checks whether the expected source document was properly cited in brackets."""
    bracket_matches = re.findall(r"\[Doc:\s*([^,\]]+)", answer)
    cited_docs = {m.strip().lower() for m in bracket_matches}
    expected_base = expected_doc.lower().split(".")[0]
    return 1.0 if any(expected_base in doc for doc in cited_docs) else 0.0


def compute_hallucination_score(answer: str, retrieved_corpus: str) -> float:
    """Estimates ungrounded entity/numerical assertions not present in evidence."""
    nums_in_answer = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", answer))
    nums_in_corpus = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", retrieved_corpus))

    if not nums_in_answer:
        return 0.0

    unsupported = nums_in_answer - nums_in_corpus
    return round(len(unsupported) / len(nums_in_answer), 2)
