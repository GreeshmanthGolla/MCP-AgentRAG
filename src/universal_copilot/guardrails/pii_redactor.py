"""PII Redactor: Detects, masks, and manages reversible token substitution."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class RedactionResult:
    redacted_text: str
    redaction_map: Dict[str, str]  # token -> original value
    detected_types: List[str] = field(default_factory=list)


PII_PATTERNS = [
    ("EMAIL", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"),
    ("PHONE", r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    ("SSN", r"\b\d{3}-\d{2}-\d{4}\b"),
    ("CREDIT_CARD", r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    ("IP_ADDRESS", r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    ("API_KEY", r"\b(?:sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z-_]{35})\b"),
]


class PIIRedactor:
    """Detects and masks sensitive PII entities."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def redact(self, text: str) -> RedactionResult:
        if not self.enabled or not text:
            return RedactionResult(redacted_text=text, redaction_map={}, detected_types=[])

        redacted = text
        redaction_map: Dict[str, str] = {}
        detected_types: List[str] = []
        counters: Dict[str, int] = {}

        for pii_type, regex in PII_PATTERNS:
            matches = re.finditer(regex, redacted)
            for m in list(matches):
                val = m.group(0)
                # Ignore common document versioning strings that match IP address
                if pii_type == "IP_ADDRESS" and (val.startswith("0.") or val.endswith(".0")):
                    continue

                if pii_type not in detected_types:
                    detected_types.append(pii_type)

                counters[pii_type] = counters.get(pii_type, 0) + 1
                token = f"[{pii_type}_{counters[pii_type]}]"
                redaction_map[token] = val
                redacted = redacted.replace(val, token)

        return RedactionResult(
            redacted_text=redacted,
            redaction_map=redaction_map,
            detected_types=detected_types,
        )

    def restore(self, text: str, redaction_map: Dict[str, str]) -> str:
        """Restores original values from redaction map."""
        restored = text
        for token, original in redaction_map.items():
            restored = restored.replace(token, original)
        return restored
