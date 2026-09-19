"""Multi-transport FastMCP Client with in-process execution fallback."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from universal_copilot.config import settings
from universal_copilot.mcp.scopes import ScopeError, ScopeValidator
from universal_copilot.mcp.tools import (
    tool_execute_query,
    tool_list_documents,
    tool_log_audit_event,
    tool_query_entity,
)


class MCPClient:
    """Client for invoking FastMCP tools with scope verification and in-process fallback."""

    def __init__(
        self,
        transport: Optional[str] = None,
        granted_scopes: Optional[List[str]] = None,
    ):
        self.transport = transport or settings().mcp.transport
        self.validator = ScopeValidator(granted_scopes)
        self._tool_handlers = {
            "query_entity": tool_query_entity,
            "list_documents": tool_list_documents,
            "execute_query": tool_execute_query,
            "log_audit_event": tool_log_audit_event,
        }

    def call_tool(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Invoke MCP tool synchronously with scope check and telemetry."""
        # 1. Scope Enforcement
        self.validator.validate_tool_access(tool_name)

        handler = self._tool_handlers.get(tool_name)
        if not handler:
            return {"status": "error", "message": f"Tool '{tool_name}' not registered."}

        t0 = time.perf_counter()
        try:
            result = handler(**kwargs)
            duration_ms = (time.perf_counter() - t0) * 1000
            return {
                "tool": tool_name,
                "status": "success",
                "duration_ms": round(duration_ms, 2),
                "data": result,
            }
        except Exception as e:
            duration_ms = (time.perf_counter() - t0) * 1000
            return {
                "tool": tool_name,
                "status": "error",
                "duration_ms": round(duration_ms, 2),
                "error": str(e),
            }
