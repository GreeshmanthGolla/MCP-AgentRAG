"""Tests for multi-tiered SQLite memory persistence (Working, Episodic, Semantic)."""
from __future__ import annotations

import pytest
from universal_copilot.memory.episodic import EpisodicMemory
from universal_copilot.memory.semantic import SemanticMemory
from universal_copilot.memory.working import WorkingMemory


def test_working_memory_scratchpad(temp_db):
    wm = WorkingMemory(temp_db)

    wm.record_step(thread_id="t-1", case_id="c-1", node="triage_node", thought="Classified intent", findings="Expense question")
    wm.record_step(thread_id="t-1", case_id="c-1", node="supervisor_node", thought="Routing to RAG", findings="Dispatching doc worker")

    pad = wm.get_scratchpad("t-1")
    assert len(pad) == 2
    assert pad[0]["node"] == "triage_node"
    assert pad[1]["node"] == "supervisor_node"

    wm.clear_thread("t-1")
    assert len(wm.get_scratchpad("t-1")) == 0


def test_episodic_memory_and_lru(temp_db):
    # Set max 3 episodes to test eviction
    em = EpisodicMemory(temp_db, max_episodes_per_entity=3)

    for i in range(5):
        em.save_episode(
            entity_id="ENT-100",
            case_id=f"CASE-{i}",
            summary=f"Resolved case {i}",
        )

    episodes = em.get_episodes("ENT-100", limit=10)
    assert len(episodes) == 3
    # Check that most recent cases (2, 3, 4) survived
    survived_ids = {e["case_id"] for e in episodes}
    assert "CASE-4" in survived_ids
    assert "CASE-3" in survived_ids


def test_semantic_memory(temp_db):
    sm = SemanticMemory(temp_db)

    sm.store_fact(
        key="sla_availability",
        category="service_levels",
        content="Core API uptime is 99.95% under SLA-2024",
        source_doc="vendor_contract.txt",
    )

    fact = sm.get_fact("sla_availability")
    assert fact is not None
    assert fact["category"] == "service_levels"
    assert "99.95%" in fact["content"]
