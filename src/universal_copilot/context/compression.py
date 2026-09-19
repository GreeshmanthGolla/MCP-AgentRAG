"""Context compression and factual abstraction."""
from __future__ import annotations

import re
from typing import Any, Dict, List
from universal_copilot.schemas import DocumentChunk


class ContextCompressor:
    """Condenses verbose document chunks and structured records while preserving numerical values and constraints."""

    @staticmethod
    def compress_chunk(chunk: DocumentChunk, max_chars: int = 600) -> str:
        text = chunk.content.strip()
        if len(text) <= max_chars:
            return text

        # Preserve key sections: headers, numbers, percentages, dates, and currency
        lines = text.splitlines()
        important_lines: List[str] = []
        for line in lines:
            if re.search(r"(SECTION|ARTICLE|CLAUSE|\$|%|\b\d+\s*(?:days?|hours?|months?|years?)\b)", line, re.IGNORECASE):
                important_lines.append(line.strip())
            elif len(important_lines) < 3:
                important_lines.append(line.strip())

        compressed = "\n".join(important_lines)
        if len(compressed) > max_chars:
            compressed = compressed[:max_chars] + "..."
        return compressed

    @staticmethod
    def compress_history(history: List[Dict[str, Any]], max_items: int = 5) -> List[Dict[str, Any]]:
        """Keeps recent case interaction summaries without verbose logs."""
        if not history:
            return []
        sorted_h = sorted(history, key=lambda x: str(x.get("date", "")), reverse=True)
        compressed = []
        for h in sorted_h[:max_items]:
            compressed.append({
                "case_id": h.get("case_id"),
                "type": h.get("type"),
                "status": h.get("status"),
                "amount": h.get("amount"),
                "date": h.get("date"),
            })
        return compressed
