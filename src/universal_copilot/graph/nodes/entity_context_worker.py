"""Entity Context Worker: Retrieves structured user/entity attributes via FastMCP."""
from __future__ import annotations

from typing import Any, Dict
from universal_copilot.mcp.client import MCPClient
from universal_copilot.state import CaseState


def entity_context_worker(state: CaseState) -> Dict[str, Any]:
    entity_id = state.get("entity_id")
    client = MCPClient()
    entity_data: Dict[str, Any] = {}

    if entity_id:
        res = client.call_tool("query_entity", entity_id=entity_id)
        if res.get("status") == "success" and res.get("data", {}).get("status") == "success":
            entity_data = res["data"]["entity"]

    findings = f"Loaded record for {entity_id} ({entity_data.get('name', 'Unknown')})" if entity_data else f"Entity {entity_id} not found"

    return {
        "entity_metadata": entity_data,
        "route": "supervisor_node",
        "visited_nodes": ["entity_context_worker"],
        "agent_scratchpad": [{
            "node": "entity_context_worker",
            "thought": f"Queried entity context for '{entity_id}'.",
            "findings": findings,
        }],
    }
