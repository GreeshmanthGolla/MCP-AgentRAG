"""Working memory: thread-scoped scratchpad persistence."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from universal_copilot.memory.store import MemoryStore


class WorkingMemory:
    """Manages ephemeral step scratchpad records during active case resolution threads."""

    def __init__(self, store: Optional[MemoryStore] = None):
        self.store = store or MemoryStore()

    def record_step(
        self,
        thread_id: str,
        case_id: str,
        node: str,
        thought: str,
        findings: str = "",
        step_index: Optional[int] = None,
    ) -> None:
        now = time.time()
        with self.store.get_connection() as conn:
            if step_index is None:
                cur = conn.execute(
                    "SELECT COALESCE(MAX(step_index), 0) + 1 FROM working_memory WHERE thread_id = ?",
                    (thread_id,),
                )
                idx = cur.fetchone()[0]
            else:
                idx = step_index

            conn.execute(
                """INSERT INTO working_memory (thread_id, case_id, step_index, node, thought, findings, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (thread_id, case_id, idx, node, thought, findings, now),
            )
            conn.commit()

    def get_scratchpad(self, thread_id: str) -> List[Dict[str, Any]]:
        with self.store.get_connection() as conn:
            rows = conn.execute(
                """SELECT step_index, node, thought, findings, created_at
                   FROM working_memory
                   WHERE thread_id = ?
                   ORDER BY step_index ASC""",
                (thread_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def clear_thread(self, thread_id: str) -> None:
        with self.store.get_connection() as conn:
            conn.execute("DELETE FROM working_memory WHERE thread_id = ?", (thread_id,))
            conn.commit()
