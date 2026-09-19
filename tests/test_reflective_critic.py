"""Tests for the Reflective Critic and self-healing corrective loop."""
from __future__ import annotations

import pytest
from universal_copilot.graph.nodes.critic_node import critic_node
from universal_copilot.schemas import DocumentChunk
from universal_copilot.state import new_case_state


def test_critic_accepts_grounded_draft():
    chunk = DocumentChunk(
        doc_id="d1",
        filename="company_policy.pdf",
        content="Expense reports must be submitted within 30 calendar days.",
    )
    state = new_case_state(
        case_id="C-GROUNDED",
        query="What is the expense submission window?",
    )
    state["retrieved_chunks"] = [chunk]
    state["draft_response"] = (
        "Under corporate guidelines [Doc: company_policy.pdf], expense reports must be submitted "
        "within 30 calendar days."
    )

    update = critic_node(state)
    assert update["is_grounded"] is True
    assert update["grounding_score"] >= 0.70
    assert update["route"] == "hitl_approval_node"


def test_critic_triggers_corrective_loop_on_missing_citations():
    chunk = DocumentChunk(
        doc_id="d1",
        filename="company_policy.pdf",
        content="Expense reports must be submitted within 30 calendar days.",
    )
    state = new_case_state(
        case_id="C-UNGROUNDED",
        query="What is the expense submission window?",
    )
    state["retrieved_chunks"] = [chunk]
    # Draft without bracketed citations
    state["draft_response"] = "You must submit your expenses promptly within some days."
    state["critic_retry_count"] = 0

    update = critic_node(state)
    assert update["is_grounded"] is False
    assert update["critic_retry_count"] == 1
    assert update["route"] == "doc_rag_worker"
    assert update["query_rewrite"] is not None


def test_critic_halts_loop_after_max_retries():
    state = new_case_state(
        case_id="C-MAX-RETRY",
        query="Some arbitrary obscure question",
    )
    state["retrieved_chunks"] = []
    state["draft_response"] = "Arbitrary ungrounded draft without citations."
    state["critic_retry_count"] = 2  # Already at max retries

    update = critic_node(state)
    # Even if ungrounded, should exit to HITL approval rather than loop infinitely
    assert update["route"] == "hitl_approval_node"
