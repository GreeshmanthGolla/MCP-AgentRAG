"""Pytest shared fixtures and test configuration."""
from __future__ import annotations

import os
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

# Force offline mode for all tests
os.environ["LLM_MODE"] = "offline"

from universal_copilot.memory.store import MemoryStore
from universal_copilot.rag.hybrid_retriever import HybridRetriever


@pytest.fixture(scope="session", autouse=True)
def ensure_sample_data():
    sample_dir = ROOT / "data" / "sample_docs"
    if not sample_dir.exists() or not list(sample_dir.glob("*.*")):
        from scripts.generate_synthetic_data import generate_all
        generate_all()


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_memory.sqlite"
    store = MemoryStore(db_path=db_file)
    return store


@pytest.fixture
def retriever(tmp_path):
    r = HybridRetriever()
    # Ingest existing sample docs
    sample_dir = ROOT / "data" / "sample_docs"
    if sample_dir.exists():
        r.ingest_directory(sample_dir)
    return r
