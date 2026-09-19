"""HITL Approval Node: Terminal human-in-the-loop gatekeeper."""
from __future__ import annotations

import time
from typing import Any, Dict
from universal_copilot.state import CaseState


def hitl_approval_node(state: CaseState) -> Dict[str, Any]:
    draft = state.get("human_modified_text") or state.get("draft_response", "")
    citations = state.get("citations", [])
    grounding = state.get("grounding_score", 1.0)
    is_escalated = state.get("requires_escalation", False)

    # Format human operator envelope
    citation_lines = [f"- {c.format_bracket()}: \"{c.quote[:100]}\"" for c in citations]
    citations_block = "\n".join(citation_lines) if citation_lines else "- No specific citations cited."

    envelope = (
        f"=== RESOLUTION SUMMARY ===\n"
        f"Status: {'ESCALATED TO HUMAN SPECIALIST' if is_escalated else 'PENDING HUMAN OPERATOR APPROVAL'}\n"
        f"Grounding Score: {grounding:.2f}\n\n"
        f"Draft Text:\n{draft}\n\n"
        f"Source Evidence Citations:\n{citations_block}\n"
        f"==========================="
    )

    # Human sign-off simulation/status
    approved = state.get("human_approved", False)
    final_resp = draft if approved else envelope

    return {
        "final_response": final_resp,
        "route": "END",
        "visited_nodes": ["hitl_approval_node"],
        "audit_events": [{
            "timestamp": time.time(),
            "event_type": "hitl_package_ready",
            "case_id": state.get("case_id"),
            "grounding": grounding,
            "escalated": is_escalated,
        }],
        "agent_scratchpad": [{
            "node": "hitl_approval_node",
            "thought": "Prepared resolution draft for human operator review.",
            "findings": "Awaiting human operator sign-off or dispatched as envelope.",
        }],
    }
