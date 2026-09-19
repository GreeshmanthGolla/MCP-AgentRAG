"""Escalation Node: Packages policy escalations for formal human review."""
from __future__ import annotations

from typing import Any, Dict
from universal_copilot.state import CaseState


def escalation_node(state: CaseState) -> Dict[str, Any]:
    reason = state.get("escalation_reason", "High-risk policy threshold breached.")
    query = state.get("sanitized_query") or state.get("raw_query") or ""
    entity_id = state.get("entity_id", "Anonymous")

    escalation_draft = (
        f"MANDATORY CASE ESCALATION NOTICE\n"
        f"Entity: {entity_id}\n"
        f"Trigger Reason: {reason}\n"
        f"Case Description: {query}\n\n"
        f"Recommendation: Route immediately to the Compliance & Legal Review Board. "
        f"Direct automated resolution is suspended pursuant to Corporate Governance Policy."
    )

    return {
        "requires_escalation": True,
        "draft_response": escalation_draft,
        "is_grounded": True,
        "route": "hitl_approval_node",
        "visited_nodes": ["escalation_node"],
        "agent_scratchpad": [{
            "node": "escalation_node",
            "thought": "Escalation draft formulated.",
            "findings": reason,
        }],
    }
