"""LangGraph Multi-Agent Topology assembly and conditional routing."""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from universal_copilot.graph.nodes.critic_node import critic_node
from universal_copilot.graph.nodes.doc_rag_worker import doc_rag_worker
from universal_copilot.graph.nodes.entity_context_worker import entity_context_worker
from universal_copilot.graph.nodes.escalation_node import escalation_node
from universal_copilot.graph.nodes.guardrail_node import blocked_exit, guardrail_node
from universal_copilot.graph.nodes.hitl_approval_node import hitl_approval_node
from universal_copilot.graph.nodes.mcp_tool_worker import mcp_tool_worker
from universal_copilot.graph.nodes.supervisor_node import supervisor_node
from universal_copilot.graph.nodes.synthesis_node import synthesis_node
from universal_copilot.graph.nodes.triage_node import triage_node
from universal_copilot.state import CaseState


def route_after_guardrail(state: CaseState) -> str:
    return "blocked_exit" if state.get("blocked") else "triage_node"


def route_from_supervisor(state: CaseState) -> str:
    r = state.get("route", "synthesis_node")
    valid = {
        "doc_rag_worker",
        "entity_context_worker",
        "mcp_tool_worker",
        "escalation_node",
        "synthesis_node",
        "hitl_approval_node",
    }
    return r if r in valid else "synthesis_node"


def route_after_critic(state: CaseState) -> str:
    r = state.get("route", "hitl_approval_node")
    return "doc_rag_worker" if r == "doc_rag_worker" else "hitl_approval_node"


def build_graph(checkpointer=None):
    """Assembles the governed LangGraph multi-agent copilot."""
    builder = StateGraph(CaseState)

    # 1. Add all 10 nodes
    builder.add_node("guardrail_node", guardrail_node)
    builder.add_node("blocked_exit", blocked_exit)
    builder.add_node("triage_node", triage_node)
    builder.add_node("supervisor_node", supervisor_node)
    builder.add_node("doc_rag_worker", doc_rag_worker)
    builder.add_node("entity_context_worker", entity_context_worker)
    builder.add_node("mcp_tool_worker", mcp_tool_worker)
    builder.add_node("escalation_node", escalation_node)
    builder.add_node("synthesis_node", synthesis_node)
    builder.add_node("critic_node", critic_node)
    builder.add_node("hitl_approval_node", hitl_approval_node)

    # 2. Entry point
    builder.set_entry_point("guardrail_node")

    # 3. Edges
    builder.add_conditional_edges(
        "guardrail_node",
        route_after_guardrail,
        {"triage_node": "triage_node", "blocked_exit": "blocked_exit"}
    )
    builder.add_edge("triage_node", "supervisor_node")

    builder.add_conditional_edges(
        "supervisor_node",
        route_from_supervisor,
        {
            "doc_rag_worker": "doc_rag_worker",
            "entity_context_worker": "entity_context_worker",
            "mcp_tool_worker": "mcp_tool_worker",
            "escalation_node": "escalation_node",
            "synthesis_node": "synthesis_node",
            "hitl_approval_node": "hitl_approval_node",
        }
    )

    # Workers report back to supervisor
    builder.add_edge("doc_rag_worker", "supervisor_node")
    builder.add_edge("entity_context_worker", "supervisor_node")
    builder.add_edge("mcp_tool_worker", "supervisor_node")
    builder.add_edge("escalation_node", "hitl_approval_node")

    # Synthesis routes to reflective critic
    builder.add_edge("synthesis_node", "critic_node")

    # Critic can route to doc_rag_worker (self-healing loop) or hitl_approval_node
    builder.add_conditional_edges(
        "critic_node",
        route_after_critic,
        {
            "doc_rag_worker": "doc_rag_worker",
            "hitl_approval_node": "hitl_approval_node",
        }
    )

    # Terminal nodes
    builder.add_edge("hitl_approval_node", END)
    builder.add_edge("blocked_exit", END)

    return builder.compile(checkpointer=checkpointer) if checkpointer else builder.compile()
