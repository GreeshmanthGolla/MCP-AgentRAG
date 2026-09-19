"""Triage Node: Intent classification and source dependency analysis."""
from __future__ import annotations

import json
from typing import Any, Dict
from universal_copilot.llm.provider import LLMProvider
from universal_copilot.state import CaseState


def triage_node(state: CaseState) -> Dict[str, Any]:
    query = state.get("sanitized_query", "")
    llm = LLMProvider(
        mode=state.get("llm_mode"),
        model=state.get("llm_model"),
        api_key=state.get("llm_api_key"),
    )

    prompt = (
        f"Analyze this case inquiry and classify intent and required resources:\n"
        f"Query: {query}\n"
        f"Return JSON with keys: intent, needs_doc_rag, needs_entity_context, needs_mcp_tools, domain"
    )
    system_prompt = "You are the Triage Agent. Output valid JSON indicating required intelligence sources."

    res = llm.generate(prompt=prompt, system_prompt=system_prompt)
    try:
        parsed = json.loads(res.text)
        plan_desc = f"Intent: {parsed.get('intent')}. Needs: docs={parsed.get('needs_doc_rag')}, entity={parsed.get('needs_entity_context')}"
    except Exception:
        plan_desc = "Triage: general retrieval and context synthesis required."

    return {
        "active_plan": plan_desc,
        "route": "supervisor_node",
        "visited_nodes": ["triage_node"],
        "agent_scratchpad": [{
            "node": "triage_node",
            "thought": "Classified query requirements.",
            "findings": plan_desc,
        }],
    }
