"""Context token pruning and redundancy elimination."""
from __future__ import annotations

import re
from typing import List


def prune_redundant_lines(text: str) -> str:
    """Removes consecutive duplicate lines, excessive empty lines, and noisy boilerplate."""
    if not text:
        return ""

    lines = [line.rstrip() for line in text.splitlines()]
    pruned: List[str] = []
    seen = set()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if pruned and pruned[-1] != "":
                pruned.append("")
            continue
        # Avoid repeat headers or repeated boilerplate clauses
        norm = re.sub(r"\s+", " ", stripped.lower())
        if len(norm) > 40 and norm in seen:
            continue
        seen.add(norm)
        pruned.append(line)

    return "\n".join(pruned).strip()


def truncate_to_token_budget(text: str, max_tokens: int = 1500) -> str:
    """Approximates 4 chars per token and truncates preserving sentence boundaries."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text

    cut = text.rfind(". ", 0, max_chars)
    if cut == -1:
        cut = text.rfind("\n", 0, max_chars)
    if cut == -1:
        cut = max_chars

    return text[:cut].strip() + " ... [TRUNCATED FOR TOKEN BUDGET]"
