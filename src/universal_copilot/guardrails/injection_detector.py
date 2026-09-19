"""Prompt Injection and Jailbreak Detector (OWASP LLM01 Defense)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class InjectionScanResult:
    is_safe: bool
    risk_score: float  # 0.0 (safe) to 1.0 (malicious)
    detected_patterns: List[str] = field(default_factory=list)
    reason: str = ""


# High-confidence prompt injection heuristics
INJECTION_SIGNATURES = [
    (r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|rules)", "Instruction override attack"),
    (r"disregard\s+(all\s+)?(previous|prior|system)\s+(instructions|directives)", "Directive override attack"),
    (r"system\s+prompt\s+override", "Explicit system override"),
    (r"you\s+are\s+now\s+in\s+developer\s+mode", "Jailbreak: developer mode"),
    (r"dan\s+mode|jailbreak|unrestricted\s+mode", "Jailbreak: persona exploit"),
    (r"repeat\s+(all\s+)?your\s+system\s+instructions", "System prompt extraction"),
    (r"output\s+the\s+preceding\s+prompt\s+verbatim", "System prompt leakage"),
    (r"reveal\s+(internal|secret|hidden)\s+system", "Confidential instruction leak"),
    (r"<system>.*?</system>", "Simulated system XML tags"),
    (r"base64\s+decode.*exec", "Obfuscated payload execution"),
]


class InjectionDetector:
    """Scans user queries and retrieved snippets for prompt injection attempts."""

    def __init__(self, sensitivity: float = 0.5):
        self.sensitivity = sensitivity

    def scan(self, text: str) -> InjectionScanResult:
        if not text:
            return InjectionScanResult(is_safe=True, risk_score=0.0)

        lower_text = text.lower()
        detected = []
        weight_sum = 0.0

        for pattern, desc in INJECTION_SIGNATURES:
            if re.search(pattern, lower_text, re.IGNORECASE):
                detected.append(desc)
                weight_sum += 0.65

        risk_score = min(1.0, weight_sum)
        is_safe = risk_score < self.sensitivity

        reason = f"Detected {len(detected)} injection signatures: {', '.join(detected)}" if detected else "Input verified safe"
        return InjectionScanResult(
            is_safe=is_safe,
            risk_score=round(risk_score, 2),
            detected_patterns=detected,
            reason=reason,
        )
