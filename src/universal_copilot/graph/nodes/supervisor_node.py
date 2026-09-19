"""Supervisor Node: Central coordinator dispatching specialist workers."""
from __future__ import annotations

from typing import Any, Dict
from universal_copilot.config import settings
from universal_copilot.state import CaseState


def supervisor_node(state: CaseState) -> Dict[str, Any]:
    query = (state.get("sanitized_query") or state.get("raw_query") or "").lower()
    visited = set(state.get("visited_nodes", []))
    policies = settings().policies
    triggers = policies.get("escalation_triggers", {}).get("sensitive_keywords", [])

    # 1. Policy Escalation Check
    for kw in triggers:
        if kw in query:
            return {
                "route": "escalation_node",
                "requires_escalation": True,
                "escalation_reason": f"Mandatory escalation policy triggered by keyword: '{kw}'",
                "visited_nodes": ["supervisor_node"],
                "agent_scratchpad": [{
                    "node": "supervisor_node",
                    "thought": f"Sensitive keyword '{kw}' detected. Routing directly to escalation handler.",
                    "findings": "Supervisor policy dispatch -> escalation_node",
                }],
            }

    # 2. Entity Context Worker Dispatch
    if state.get("entity_id") and not state.get("entity_metadata") and "entity_context_worker" not in visited:
        return {
            "route": "entity_context_worker",
            "visited_nodes": ["supervisor_node"],
            "agent_scratchpad": [{
                "node": "supervisor_node",
                "thought": "Entity ID provided without metadata. Dispatching entity context worker.",
                "findings": "Supervisor dispatch -> entity_context_worker",
            }],
        }

    # 3. Document RAG Worker Dispatch
    if (not state.get("retrieved_chunks") or state.get("query_rewrite")) and "doc_rag_worker" not in visited:
        return {
            "route": "doc_rag_worker",
            "visited_nodes": ["supervisor_node"],
            "agent_scratchpad": [{
                "node": "supervisor_node",
                "thought": "Knowledge retrieval required. Dispatching document RAG worker.",
                "findings": "Supervisor dispatch -> doc_rag_worker",
            }],
        }

    # 4. MCP Tool Worker Dispatch (if query needs structured data lookups)
    if any(k in query for k in ["catalog", "sku", "roster", "database", "record"]) and "mcp_tool_worker" not in visited:
        return {
            "route": "mcp_tool_worker",
            "visited_nodes": ["supervisor_node"],
            "agent_scratchpad": [{
                "node": "supervisor_node",
                "thought": "Structured database search requested. Dispatching MCP tool worker.",
                "findings": "Supervisor dispatch -> mcp_tool_worker",
            }],
        }

    # 5. Synthesis Worker Dispatch
    return {
        "route": "synthesis_node",
        "visited_nodes": ["supervisor_node"],
        "agent_scratchpad": [{
            "node": "supervisor_node",
            "thought": "All requisite context gathered. Proceeding to draft synthesis.",
            "findings": "Supervisor dispatch -> synthesis_node",
        }],
    }
