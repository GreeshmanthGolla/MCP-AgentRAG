"""End-to-end tests across diverse enterprise domains (Expense, SLA, Legal Escalation, Product)."""
from __future__ import annotations

import pytest
from universal_copilot.graph.runner import run_case_sync


def test_e2e_expense_case():
    res = run_case_sync(
        query="What is the expense submission window, and can an expense from 75 days ago be reimbursed?",
        entity_id="ENT-1001",
    )
    assert not res.requires_escalation
    assert res.is_grounded
    assert "30 calendar days" in res.final_response or "30 days" in res.final_response
    assert "forfeited" in res.final_response.lower()
    assert len(res.citations) > 0


def test_e2e_vendor_sla_case():
    res = run_case_sync(
        query="Our database uptime dropped to 98.6%. What service credit are we owed under MSA-2024-8891?",
        entity_id="ENT-1002",
    )
    assert not res.requires_escalation
    assert res.is_grounded
    assert "25%" in res.final_response
    assert len(res.citations) > 0


def test_e2e_harassment_mandatory_escalation():
    res = run_case_sync(
        query="I am experiencing workplace harassment and retaliation from my supervisor after reporting accounting irregularities.",
        entity_id="ENT-1001",
    )
    assert res.requires_escalation
    assert "escalation_node" in res.visited_nodes
    assert "MANDATORY CASE ESCALATION" in res.final_response or "Legal & Compliance" in res.final_response


def test_e2e_product_catalog_case():
    res = run_case_sync(
        query="Can we request a full refund for Cloud Data Lake Enterprise 20 days after deployment?",
        entity_id="ENT-1003",
    )
    assert not res.requires_escalation
    assert res.is_grounded
    assert "30 days" in res.final_response
