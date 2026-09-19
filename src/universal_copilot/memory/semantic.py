"""Semantic memory: long-term fact store and indexed knowledge."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from universal_copilot.memory.store import MemoryStore


class SemanticMemory:
    """Stores persistent reference facts, summaries, and domain definitions."""

    def __init__(self, store: Optional[MemoryStore] = None):
        self.store = store or MemoryStore()

    def store_fact(
        self,
        key: str,
        category: str,
        content: str,
        source_doc: Optional[str] = None,
    ) -> None:
        now = time.time()
        with self.store.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO semantic_memory (key, category, content, source_doc, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (key, category, content, source_doc, now),
            )
            conn.commit()

    def get_fact(self, key: str) -> Optional[Dict[str, Any]]:
        with self.store.get_connection() as conn:
            row = conn.execute(
                "SELECT key, category, content, source_doc, updated_at FROM semantic_memory WHERE key = ?",
                (key,),
            ).fetchone()
            return dict(row) if row else None

    def query_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        with self.store.get_connection() as conn:
            rows = conn.execute(
                """SELECT key, category, content, source_doc, updated_at
                   FROM semantic_memory
                   WHERE category = ?
                   ORDER BY updated_at DESC
                   LIMIT ?""",
                (category, limit),
            ).fetchall()
            return [dict(r) for r in rows]
