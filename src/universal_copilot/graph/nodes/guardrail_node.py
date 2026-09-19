"""Guardrail Node: Prompt injection detection and PII masking."""
from __future__ import annotations

from typing import Any, Dict
from universal_copilot.guardrails.injection_detector import InjectionDetector
from universal_copilot.guardrails.pii_redactor import PIIRedactor
from universal_copilot.state import CaseState


def guardrail_node(state: CaseState) -> Dict[str, Any]:
    query = state.get("raw_query", "")
    detector = InjectionDetector()
    redactor = PIIRedactor()

    # 1. Scan for prompt injection
    scan_res = detector.scan(query)
    if not scan_res.is_safe:
        return {
            "blocked": True,
            "block_reason": f"Prompt injection detected: {scan_res.reason}",
            "route": "blocked_exit",
            "visited_nodes": ["guardrail_node"],
            "agent_scratchpad": [{
                "node": "guardrail_node",
                "thought": "Malicious prompt pattern detected. Aborting execution pipeline.",
                "findings": scan_res.reason,
            }],
        }

    # 2. Mask sensitive PII
    redaction_res = redactor.redact(query)

    return {
        "blocked": False,
        "sanitized_query": redaction_res.redacted_text,
        "redaction_map": redaction_res.redaction_map,
        "route": "triage_node",
        "visited_nodes": ["guardrail_node"],
        "agent_scratchpad": [{
            "node": "guardrail_node",
            "thought": "Input verified safe.",
            "findings": f"PII masked: {redaction_res.detected_types}" if redaction_res.detected_types else "No PII found",
        }],
    }


def blocked_exit(state: CaseState) -> Dict[str, Any]:
    """Terminal node for safety and policy violations."""
    reason = state.get("block_reason", "Security policy violation detected.")
    return {
        "final_response": f"REQUEST BLOCKED: {reason}",
        "visited_nodes": ["blocked_exit"],
        "route": "END",
    }
