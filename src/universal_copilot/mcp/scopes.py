"""Scope-based access control for FastMCP tools and resources."""
from __future__ import annotations

from typing import List, Set


class ScopeError(PermissionError):
    """Raised when an operation violates authorized MCP scopes."""
    pass


class ScopeValidator:
    """Enforces fine-grained scope authorization for MCP operations."""

    DEFAULT_ALLOWED_SCOPES = {
        "read:docs",
        "read:entity",
        "write:audit",
        "execute:query",
    }

    TOOL_REQUIRED_SCOPES = {
        "query_entity": "read:entity",
        "list_documents": "read:docs",
        "execute_query": "execute:query",
        "log_audit_event": "write:audit",
    }

    def __init__(self, granted_scopes: Optional[List[str] | Set[str]] = None):
        self.granted_scopes = set(granted_scopes) if granted_scopes is not None else set(self.DEFAULT_ALLOWED_SCOPES)

    def validate_tool_access(self, tool_name: str) -> None:
        required = self.TOOL_REQUIRED_SCOPES.get(tool_name)
        if required and required not in self.granted_scopes:
            raise ScopeError(
                f"Access denied to tool '{tool_name}'. Required scope '{required}' is not in granted scopes {sorted(self.granted_scopes)}."
            )
