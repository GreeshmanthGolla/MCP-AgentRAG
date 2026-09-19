"""SQLite backing store and database migrations for tiered memory."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional
from universal_copilot.config import settings


SCHEMA_SQL = """
-- Working memory: per-thread agent step scratchpad
CREATE TABLE IF NOT EXISTS working_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    node TEXT NOT NULL,
    thought TEXT,
    findings TEXT,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_working_thread ON working_memory(thread_id);

-- Episodic memory: per-entity/case historical interactions
CREATE TABLE IF NOT EXISTS episodic_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    metadata_json TEXT,
    last_accessed REAL NOT NULL,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_episodic_entity ON episodic_memory(entity_id);

-- Semantic memory: long-term document summaries and facts
CREATE TABLE IF NOT EXISTS semantic_memory (
    key TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    source_doc TEXT,
    embedding_json TEXT,
    updated_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_semantic_cat ON semantic_memory(category);

-- Audit log: immutable compliance record
CREATE TABLE IF NOT EXISTS audit_logs (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    user_or_entity TEXT NOT NULL,
    details_json TEXT NOT NULL,
    timestamp REAL NOT NULL
);
"""


class MemoryStore:
    """Thread-safe SQLite database manager for Universal Copilot memory tiers."""

    def __init__(self, db_path: Optional[Path | str] = None):
        cfg_path = db_path or settings().sqlite_db_path
        self.db_path = Path(cfg_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def init_db(self) -> None:
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def clear(self) -> None:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM working_memory;")
            conn.execute("DELETE FROM episodic_memory;")
            conn.execute("DELETE FROM semantic_memory;")
            conn.execute("DELETE FROM audit_logs;")
            conn.commit()
