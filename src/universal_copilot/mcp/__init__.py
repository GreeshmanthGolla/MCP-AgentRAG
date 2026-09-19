"""Model Context Protocol (FastMCP) integration package."""

from universal_copilot.mcp.client import MCPClient
from universal_copilot.mcp.scopes import ScopeError, ScopeValidator
from universal_copilot.mcp.server import mcp_server, start_server

__all__ = [
    "MCPClient",
    "ScopeError",
    "ScopeValidator",
    "mcp_server",
    "start_server",
]
