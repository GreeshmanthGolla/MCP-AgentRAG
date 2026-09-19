"""Typed LangGraph State and state factories for Universal Document Copilot."""
from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from universal_copilot.schemas import Citation, DocumentChunk


class CaseState(TypedDict, total=False):
    # Core identifiers
    case_id: str
    user_id: Optional[str]
    thread_id: str

    # Queries & Guardrails
    raw_query: str
    sanitized_query: str
    blocked: bool
    block_reason: Optional[str]
    redaction_map: Dict[str, str]

    # Dynamic context & attachments
    entity_id: Optional[str]
    entity_metadata: Dict[str, Any]
    target_docs: List[str]

    # Graph flow & execution
    route: str
    visited_nodes: Annotated[List[str], operator.add]
    active_plan: Optional[str]
    agent_scratchpad: Annotated[List[Dict[str, Any]], operator.add]

    # Retrieval & Evidence
    retrieved_chunks: Annotated[List[DocumentChunk], operator.add]
    citations: List[Citation]
    query_rewrite: Optional[str]

    # Draft synthesis & Reflection
    draft_response: Optional[str]
    is_grounded: bool
    hallucination_score: float
    critic_retry_count: int
    critic_feedback: Optional[str]

    # Escalation & Governance
    requires_escalation: bool
    escalation_reason: Optional[str]

    # HITL Sign-off & Terminus
    human_approved: bool
    human_modified_text: Optional[str]
    final_response: Optional[str]

    # Telemetry & Auditing
    audit_events: Annotated[List[Dict[str, Any]], operator.add]
    tokens_used: int
    latency_ms: float

    # Dynamic LLM Model Configuration
    llm_mode: Optional[str]
    llm_model: Optional[str]
    llm_api_key: Optional[str]


def new_case_state(
    case_id: str,
    query: str,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    target_docs: Optional[List[str]] = None,
    entity_metadata: Optional[Dict[str, Any]] = None,
    llm_mode: Optional[str] = None,
    llm_model: Optional[str] = None,
    llm_api_key: Optional[str] = None,
) -> CaseState:
    """Instantiate a standardized, initialized CaseState."""
    return {
        "case_id": case_id,
        "user_id": user_id or entity_id,
        "thread_id": f"thread_{case_id}",
        "raw_query": query,
        "sanitized_query": query,
        "blocked": False,
        "block_reason": None,
        "redaction_map": {},
        "entity_id": entity_id,
        "entity_metadata": entity_metadata or {},
        "target_docs": target_docs or [],
        "llm_mode": llm_mode,
        "llm_model": llm_model,
        "llm_api_key": llm_api_key,
        "route": "guardrail_node",
        "visited_nodes": [],
        "active_plan": None,
        "agent_scratchpad": [],
        "retrieved_chunks": [],
        "citations": [],
        "query_rewrite": None,
        "draft_response": None,
        "is_grounded": False,
        "hallucination_score": 0.0,
        "critic_retry_count": 0,
        "critic_feedback": None,
        "requires_escalation": False,
        "escalation_reason": None,
        "human_approved": False,
        "human_modified_text": None,
        "final_response": None,
        "audit_events": [],
        "tokens_used": 0,
        "latency_ms": 0.0,
    }
