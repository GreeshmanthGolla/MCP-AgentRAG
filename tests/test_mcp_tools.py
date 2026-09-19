"""Tests for FastMCP tools, scopes, and client invocation."""
from __future__ import annotations

import pytest
from universal_copilot.mcp.client import MCPClient
from universal_copilot.mcp.scopes import ScopeError, ScopeValidator


def test_mcp_client_tool_calls():
    client = MCPClient(granted_scopes=["read:docs", "read:entity", "execute:query", "write:audit"])

    # 1. Query entity
    res_ent = client.call_tool("query_entity", entity_id="ENT-1001")
    assert res_ent["status"] == "success"
    assert res_ent["data"]["status"] == "success"
    assert "Aarti" in res_ent["data"]["entity"]["name"]

    # 2. List documents
    res_docs = client.call_tool("list_documents")
    assert res_docs["status"] == "success"
    filenames = [d["filename"] for d in res_docs["data"]]
    assert any("company_policy" in f for f in filenames)

    # 3. Execute query
    res_query = client.call_tool("execute_query", query_str="Cloud Data Lake")
    assert res_query["status"] == "success"
    assert res_query["data"]["match_count"] >= 1

    # 4. Log audit event
    res_audit = client.call_tool("log_audit_event", event_type="test_run", user_or_entity="ENT-1001", details={"status": "ok"})
    assert res_audit["status"] == "success"
    assert res_audit["data"]["status"] == "recorded"


def test_mcp_scope_enforcement():
    # Client missing 'write:audit'
    restricted_client = MCPClient(granted_scopes=["read:docs"])

    with pytest.raises(ScopeError) as exc_info:
        restricted_client.call_tool("log_audit_event", event_type="test", user_or_entity="ENT-1001", details={})
    assert "write:audit" in str(exc_info.value)
