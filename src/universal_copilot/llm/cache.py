"""Sub-millisecond persistent LLM response cache using prompt hashing."""
from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional
from universal_copilot.config import settings


class ResponseCache:
    """Prompt hash cache serving repeat queries with zero token cost."""

    def __init__(self, db_path: Optional[Path | str] = None):
        cfg_path = db_path or settings().llm_cache_path
        self.db_path = Path(cfg_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self.hits: int = 0
        self.misses: int = 0
        self.init_db()

    def init_db(self) -> None:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS response_cache (
                        cache_key TEXT PRIMARY KEY,
                        model TEXT NOT NULL,
                        system_prompt TEXT,
                        user_prompt TEXT NOT NULL,
                        response_text TEXT NOT NULL,
                        prompt_tokens INTEGER,
                        completion_tokens INTEGER,
                        created_at REAL NOT NULL
                    )"""
                )
                conn.commit()
        except Exception:
            pass

    def compute_key(self, model: str, system_prompt: str, user_prompt: str) -> str:
        # Normalize dynamic case/session IDs so queries match predictably
        norm_prompt = re.sub(r"CASE-[A-Za-z0-9\-_]+", "<CASE_ID>", user_prompt)
        norm_prompt = re.sub(r"thread_[A-Za-z0-9\-_]+", "<THREAD_ID>", norm_prompt)
        combined = f"{model}::{system_prompt.strip()}::{norm_prompt.strip()}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        # Check in-memory fast tier
        if cache_key in self._memory_cache:
            self.hits += 1
            return self._memory_cache[cache_key]

        # Check SQLite persistence
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                row = conn.execute(
                    """SELECT response_text, prompt_tokens, completion_tokens, model, created_at
                       FROM response_cache WHERE cache_key = ?""",
                    (cache_key,),
                ).fetchone()
                if row:
                    self.hits += 1
                    res = {
                        "text": row[0],
                        "prompt_tokens": row[1],
                        "completion_tokens": row[2],
                        "model": row[3],
                        "created_at": row[4],
                        "cached": True,
                    }
                    self._memory_cache[cache_key] = res
                    return res
        except Exception:
            pass
        self.misses += 1
        return None

    def set(
        self,
        cache_key: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response_text: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        now = time.time()
        record = {
            "text": response_text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model": model,
            "created_at": now,
            "cached": True,
        }
        self._memory_cache[cache_key] = record

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO response_cache
                       (cache_key, model, system_prompt, user_prompt, response_text, prompt_tokens, completion_tokens, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (cache_key, model, system_prompt, user_prompt, response_text, prompt_tokens, completion_tokens, now),
                )
                conn.commit()
        except Exception:
            pass

    def clear(self) -> None:
        self._memory_cache.clear()
        self.hits = 0
        self.misses = 0
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("DELETE FROM response_cache")
                conn.commit()
        except Exception:
            pass

    def stats(self) -> Dict[str, Any]:
        count = 0
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                row = conn.execute("SELECT count(*) FROM response_cache").fetchone()
                if row:
                    count = row[0]
        except Exception:
            count = len(self._memory_cache)
        total = self.hits + self.misses
        hit_ratio = (self.hits / total) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": hit_ratio,
            "total_cached_entries": count,
            "in_memory_entries": len(self._memory_cache),
        }


RESPONSE_CACHE = ResponseCache()
