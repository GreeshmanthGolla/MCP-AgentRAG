"""Vector Store with dual dense embeddings (SentenceTransformers + Deterministic Hash fallback)."""
from __future__ import annotations

import hashlib
import math
import re
from typing import Any, Dict, List, Optional, Tuple
from universal_copilot.schemas import DocumentChunk


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class EmbeddingEngine:
    """Provides vector embeddings with local deterministic fallback."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dim: int = 384):
        self.model_name = model_name
        self.dim = dim
        self._st_model = None
        self._try_load_st()

    def _try_load_st(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            self._st_model = SentenceTransformer(self.model_name)
        except Exception:
            self._st_model = None

    def embed(self, text: str) -> List[float]:
        if self._st_model is not None:
            try:
                vec = self._st_model.encode(text, convert_to_numpy=True).tolist()
                return [float(x) for x in vec]
            except Exception:
                pass
        return self._hash_embed(text)

    def _hash_embed(self, text: str) -> List[float]:
        """Deterministic hash-based dense vector for offline reproducibility."""
        vec = [0.0] * self.dim
        tokens = re.findall(r"\w+", (text or "").lower())
        if not tokens:
            return vec

        for t in tokens:
            # Deterministic hash to bucket
            h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if ((h >> 8) & 1) == 1 else -1.0
            vec[idx] += sign

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


class InMemoryVectorStore:
    """In-memory dense vector store with cosine search and metadata filtering."""

    def __init__(self, embedding_engine: Optional[EmbeddingEngine] = None):
        self.engine = embedding_engine or EmbeddingEngine()
        self.chunks: List[DocumentChunk] = []
        self.embeddings: List[List[float]] = []

    def clear(self) -> None:
        self.chunks.clear()
        self.embeddings.clear()

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        for chunk in chunks:
            emb = self.engine.embed(chunk.content)
            self.chunks.append(chunk)
            self.embeddings.append(emb)

    def search(
        self,
        query: str,
        top_k: int = 5,
        target_docs: Optional[List[str]] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        if not self.chunks:
            return []

        q_emb = self.engine.embed(query)
        scored: List[Tuple[DocumentChunk, float]] = []

        for chunk, emb in zip(self.chunks, self.embeddings):
            if target_docs and chunk.filename not in target_docs and chunk.doc_id not in target_docs:
                continue
            sim = cosine_similarity(q_emb, emb)
            scored.append((chunk, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
