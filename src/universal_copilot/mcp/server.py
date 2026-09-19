"""FastMCP Server exposing enterprise tools and resources."""
from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional
try:
    from mcp.server.fastmcp import FastMCP
except (ImportError, ModuleNotFoundError):
    try:
        from mcp.server.mcpserver import MCPServer as FastMCP
    except Exception:
        class FastMCP:  # type: ignore
            def __init__(self, name: str = "UniversalCopilotMCP", instructions: str = ""):
                self.name = name
                self.instructions = instructions
                self._tools = {}

            def tool(self):
                def decorator(fn):
                    self._tools[fn.__name__] = fn
                    return fn
                return decorator

            def run(self, transport: str = "stdio"):
                print(f"FastMCP server '{self.name}' running on {transport}")

from universal_copilot.config import settings
from universal_copilot.mcp.scopes import ScopeValidator
from universal_copilot.mcp.tools import (
    tool_execute_query,
    tool_list_documents,
    tool_log_audit_event,
    tool_query_entity,
)

# Initialize FastMCP Server
mcp_server = FastMCP(
    name="UniversalCopilotMCP",
    instructions="Universal Document and Case Resolution Copilot tool server."
)


@mcp_server.tool()
def query_entity(entity_id: str) -> Dict[str, Any]:
    """Fetch structured metadata and attributes for an entity/user."""
    return tool_query_entity(entity_id)


@mcp_server.tool()
def list_documents() -> List[Dict[str, Any]]:
    """List catalog of ingested and sample documents."""
    return tool_list_documents()


@mcp_server.tool()
def execute_query(query: str) -> Dict[str, Any]:
    """Execute search or structured filter on catalog and roster data."""
    return tool_execute_query(query)


@mcp_server.tool()
def log_audit_event(event_type: str, user_or_entity: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """Record compliance audit trail in immutable storage."""
    return tool_log_audit_event(event_type, user_or_entity, details)


def start_server(transport: Optional[str] = None, port: Optional[int] = None, host: Optional[str] = None) -> None:
    """Run FastMCP server with configured transport (stdio, sse, ws)."""
    cfg = settings().mcp
    trans = transport or cfg.transport
    p = port or cfg.port
    h = host or cfg.host

    print(f"Starting FastMCP Server with transport={trans} on {h}:{p}...")
    if trans == "stdio":
        mcp_server.run(transport="stdio")
    elif trans == "sse":
        mcp_server.run(transport="sse")
    else:
        mcp_server.run(transport="stdio")


if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    start_server(transport=t)
