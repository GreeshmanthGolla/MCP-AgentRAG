"""End-to-end runner and execution coordinator for Universal Copilot cases."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

from universal_copilot.graph.build import build_graph
from universal_copilot.memory.store import MemoryStore
from universal_copilot.memory.working import WorkingMemory
from universal_copilot.schemas import Citation, DocumentChunk
from universal_copilot.state import CaseState, new_case_state


@dataclass
class CaseExecutionResult:
    case_id: str
    query: str
    state: CaseState
    final_response: str
    citations: List[Citation]
    retrieved_chunks: List[DocumentChunk]
    is_grounded: bool
    requires_escalation: bool
    duration_ms: float
    visited_nodes: List[str]


def run_case_sync(
    query: str,
    case_id: Optional[str] = None,
    entity_id: Optional[str] = None,
    target_docs: Optional[List[str]] = None,
    store: Optional[MemoryStore] = None,
    llm_mode: Optional[str] = None,
    llm_model: Optional[str] = None,
    llm_api_key: Optional[str] = None,
) -> CaseExecutionResult:
    cid = case_id or f"CASE-{int(time.time() * 1000) % 100000}"
    init_state = new_case_state(
        case_id=cid,
        query=query,
        entity_id=entity_id,
        target_docs=target_docs,
        llm_mode=llm_mode,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
    )

    t0 = time.perf_counter()
    graph = build_graph()
    final_state: CaseState = graph.invoke(init_state)
    duration_ms = (time.perf_counter() - t0) * 1000

    # Record scratchpad to working memory
    ms = store or MemoryStore()
    wm = WorkingMemory(ms)
    for idx, item in enumerate(final_state.get("agent_scratchpad", [])):
        wm.record_step(
            thread_id=final_state.get("thread_id", f"thread_{cid}"),
            case_id=cid,
            node=item.get("node", "step"),
            thought=item.get("thought", ""),
            findings=item.get("findings", ""),
            step_index=idx + 1,
        )

    return CaseExecutionResult(
        case_id=cid,
        query=query,
        state=final_state,
        final_response=final_state.get("final_response", ""),
        citations=final_state.get("citations", []),
        retrieved_chunks=final_state.get("retrieved_chunks", []),
        is_grounded=final_state.get("is_grounded", False),
        requires_escalation=final_state.get("requires_escalation", False),
        duration_ms=round(duration_ms, 2),
        visited_nodes=final_state.get("visited_nodes", []),
    )


async def run_case(
    query: str,
    case_id: Optional[str] = None,
    entity_id: Optional[str] = None,
    target_docs: Optional[List[str]] = None,
    llm_mode: Optional[str] = None,
    llm_model: Optional[str] = None,
    llm_api_key: Optional[str] = None,
) -> CaseExecutionResult:
    return run_case_sync(
        query=query,
        case_id=case_id,
        entity_id=entity_id,
        target_docs=target_docs,
        llm_mode=llm_mode,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
    )


async def stream_case(
    query: str,
    case_id: Optional[str] = None,
    entity_id: Optional[str] = None,
    target_docs: Optional[List[str]] = None,
    llm_mode: Optional[str] = None,
    llm_model: Optional[str] = None,
    llm_api_key: Optional[str] = None,
) -> AsyncIterator[Dict[str, Any]]:
    cid = case_id or f"CASE-{int(time.time() * 1000) % 100000}"
    init_state = new_case_state(
        case_id=cid,
        query=query,
        entity_id=entity_id,
        target_docs=target_docs,
        llm_mode=llm_mode,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
    )

    graph = build_graph()
    yield {"event": "start", "case_id": cid, "query": query}

    async for chunk in graph.astream(init_state):
        for node_name, delta in chunk.items():
            yield {
                "event": "node_execution",
                "node": node_name,
                "route": delta.get("route"),
                "draft": bool(delta.get("draft_response")),
                "citations": len(delta.get("citations", [])),
                "is_grounded": delta.get("is_grounded"),
                "scratchpad": delta.get("agent_scratchpad"),
            }

    yield {"event": "done", "case_id": cid}
