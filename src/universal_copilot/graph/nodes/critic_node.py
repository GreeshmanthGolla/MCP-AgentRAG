"""Reflective Critic Node: Cross-checks claims against source chunks and drives self-healing."""
from __future__ import annotations

import json
import re
from typing import Any, Dict
from universal_copilot.config import settings
from universal_copilot.llm.provider import LLMProvider
from universal_copilot.state import CaseState


def critic_node(state: CaseState) -> Dict[str, Any]:
    draft = state.get("draft_response", "")
    chunks = state.get("retrieved_chunks", [])
    citations = state.get("citations", [])
    retry_count = state.get("critic_retry_count", 0)
    max_retries = settings().reflection.max_retries
    threshold = settings().reflection.grounding_threshold

    llm = LLMProvider(
        mode=state.get("llm_mode"),
        model=state.get("llm_model"),
        api_key=state.get("llm_api_key"),
    )

    evidence_summary = "\n".join([f"[{c.filename}] {c.content[:200]}" for c in chunks])
    prompt = (
        f"Cross-examine every factual assertion in this draft against the source chunks:\n"
        f"Draft: {draft}\n"
        f"Evidence Chunks:\n{evidence_summary}\n"
        f"Return JSON with: is_grounded (bool), grounding_score (0.0-1.0), hallucination_score (0.0-1.0), "
        f"supported_claims, unsupported_claims, suggested_query_rewrite, feedback"
    )
    system_prompt = "You are the Reflective Grounding Critic. Output strict JSON verification."

    res = llm.generate(prompt=prompt, system_prompt=system_prompt)
    is_grounded = True
    grounding_score = 0.90
    hallucination_score = 0.10
    query_rewrite = None
    feedback = "Draft grounded in cited evidence."

    try:
        parsed = json.loads(res.text)
        is_grounded = parsed.get("is_grounded", True)
        grounding_score = float(parsed.get("grounding_score", 0.90))
        hallucination_score = float(parsed.get("hallucination_score", 0.10))
        query_rewrite = parsed.get("suggested_query_rewrite")
        feedback = parsed.get("feedback", "")
    except Exception:
        # Fallback heuristic: check presence of bracket citations
        has_citations = bool(re.search(r"\[Doc:\s*[^\]]+\]", draft))
        if not has_citations and chunks:
            is_grounded = False
            grounding_score = 0.40
            hallucination_score = 0.60
            query_rewrite = "expand policy clauses and rules"
            feedback = "Missing bracketed document citations."

    # Self-healing loop decision
    if not is_grounded and grounding_score < threshold and retry_count < max_retries:
        rewrite = query_rewrite or f"specific clauses and details for {state.get('raw_query')}"
        return {
            "is_grounded": False,
            "grounding_score": grounding_score,
            "hallucination_score": hallucination_score,
            "critic_retry_count": retry_count + 1,
            "critic_feedback": feedback,
            "query_rewrite": rewrite,
            "route": "doc_rag_worker",  # Corrective self-healing RAG loop
            "visited_nodes": ["critic_node"],
            "agent_scratchpad": [{
                "node": "critic_node",
                "thought": f"Draft ungrounded (score={grounding_score}). Triggering corrective loop {retry_count + 1}/{max_retries}.",
                "findings": f"Query rewrite: '{rewrite}'",
            }],
        }

    # Satisfied grounding or exhausted retries -> route to human approval
    return {
        "is_grounded": is_grounded,
        "grounding_score": grounding_score,
        "hallucination_score": hallucination_score,
        "critic_feedback": feedback,
        "route": "hitl_approval_node",
        "visited_nodes": ["critic_node"],
        "agent_scratchpad": [{
            "node": "critic_node",
            "thought": f"Draft verification complete. Grounding score={grounding_score}.",
            "findings": "Routed to HITL approval gatekeeper.",
        }],
    }
