"""Episodic memory: scoped per entity/case history with LRU eviction."""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
from universal_copilot.memory.store import MemoryStore


class EpisodicMemory:
    """Stores past interactions for each entity with bounded LRU eviction."""

    def __init__(self, store: Optional[MemoryStore] = None, max_episodes_per_entity: int = 25):
        self.store = store or MemoryStore()
        self.max_episodes = max_episodes_per_entity

    def save_episode(
        self,
        entity_id: str,
        case_id: str,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = time.time()
        meta_json = json.dumps(metadata or {})
        with self.store.get_connection() as conn:
            conn.execute(
                """INSERT INTO episodic_memory (entity_id, case_id, summary, metadata_json, last_accessed, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (entity_id, case_id, summary, meta_json, now, now),
            )
            # LRU Eviction if count exceeds max_episodes
            conn.execute(
                """DELETE FROM episodic_memory
                   WHERE entity_id = ?
                     AND id NOT IN (
                         SELECT id FROM episodic_memory
                         WHERE entity_id = ?
                         ORDER BY last_accessed DESC
                         LIMIT ?
                     )""",
                (entity_id, entity_id, self.max_episodes),
            )
            conn.commit()

    def get_episodes(self, entity_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        now = time.time()
        with self.store.get_connection() as conn:
            rows = conn.execute(
                """SELECT id, case_id, summary, metadata_json, created_at
                   FROM episodic_memory
                   WHERE entity_id = ?
                   ORDER BY last_accessed DESC
                   LIMIT ?""",
                (entity_id, limit),
            ).fetchall()

            episodes = []
            for r in rows:
                episodes.append({
                    "id": r["id"],
                    "case_id": r["case_id"],
                    "summary": r["summary"],
                    "metadata": json.loads(r["metadata_json"] or "{}"),
                    "created_at": r["created_at"],
                })

            # Update last_accessed for LRU tracking
            if episodes:
                ids = [str(e["id"]) for e in episodes]
                conn.execute(
                    f"UPDATE episodic_memory SET last_accessed = ? WHERE id IN ({','.join(ids)})",
                    (now,),
                )
                conn.commit()

            return episodes
