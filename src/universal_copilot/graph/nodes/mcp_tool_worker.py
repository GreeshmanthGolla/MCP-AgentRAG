"""MCP Tool Worker: Dispatches authorized external tool calls."""
from __future__ import annotations

from typing import Any, Dict
from universal_copilot.mcp.client import MCPClient
from universal_copilot.state import CaseState


def mcp_tool_worker(state: CaseState) -> Dict[str, Any]:
    query = state.get("sanitized_query") or state.get("raw_query") or ""
    client = MCPClient()

    # Execute structured query tool
    tool_res = client.call_tool("execute_query", query_str=query)
    match_count = tool_res.get("data", {}).get("match_count", 0)
    findings = f"MCP tool execute_query found {match_count} structured matches."

    return {
        "route": "supervisor_node",
        "visited_nodes": ["mcp_tool_worker"],
        "agent_scratchpad": [{
            "node": "mcp_tool_worker",
            "thought": "Invoked FastMCP tool execute_query.",
            "findings": findings,
        }],
    }
