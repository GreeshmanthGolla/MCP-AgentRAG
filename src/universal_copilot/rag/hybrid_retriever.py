"""Corrective Hybrid Retriever (BM25 + Cosine Dense Vector Search + RRF)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rank_bm25 import BM25Okapi

from universal_copilot.config import settings
from universal_copilot.ingestion.chunker import DocumentChunker
from universal_copilot.ingestion.loader import DocumentLoader
from universal_copilot.rag.reranker import Reranker
from universal_copilot.rag.vector_store import InMemoryVectorStore
from universal_copilot.schemas import Citation, DocumentChunk


_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")
_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "and", "or", "of", "to", "in", "for", "on",
    "my", "me", "i", "you", "your", "can", "do", "does", "what", "how", "much", "please",
    "it", "be", "will", "if", "am", "this", "that", "at", "by", "with", "from"
}


def tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN_PATTERN.findall((text or "").lower()) if t not in _STOP_WORDS and len(t) > 1]


class HybridRetriever:
    """Hybrid BM25 and Dense Vector search engine with query rewriting and RRF fusion."""

    def __init__(
        self,
        loader: Optional[DocumentLoader] = None,
        chunker: Optional[DocumentChunker] = None,
        vector_store: Optional[InMemoryVectorStore] = None,
        reranker: Optional[Reranker] = None,
    ):
        s = settings().retrieval
        self.loader = loader or DocumentLoader()
        self.chunker = chunker or DocumentChunker()
        self.vector_store = vector_store or InMemoryVectorStore()
        self.reranker = reranker or Reranker(rrf_k=s.rrf_k, relevance_floor=s.relevance_floor)
        self.bm25_weight = s.bm25_weight
        self.vector_weight = s.vector_weight
        self.top_k = s.top_k

        self.chunks: List[DocumentChunk] = []
        self.bm25: Optional[BM25Okapi] = None
        self.tokenized_corpus: List[List[str]] = []

    def clear(self) -> None:
        self.chunks.clear()
        self.tokenized_corpus.clear()
        self.bm25 = None
        self.vector_store.clear()

    def ingest_file(self, file_path: str | Path) -> List[DocumentChunk]:
        doc = self.loader.load(file_path)
        new_chunks = self.chunker.chunk_document(doc)
        self.add_chunks(new_chunks)
        return new_chunks

    def ingest_directory(self, dir_path: str | Path) -> int:
        p = Path(dir_path)
        if not p.exists():
            return 0
        total_chunks = 0
        for f in sorted(p.iterdir()):
            if f.is_file() and self.loader.is_supported(f):
                try:
                    chunks = self.ingest_file(f)
                    total_chunks += len(chunks)
                except Exception:
                    pass
        return total_chunks

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        self.chunks.extend(chunks)
        self.vector_store.add_chunks(chunks)
        # Re-index BM25
        self.tokenized_corpus = [tokenize(c.content) for c in self.chunks]
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        target_docs: Optional[List[str]] = None,
    ) -> List[DocumentChunk]:
        k = top_k or self.top_k
        if not self.chunks:
            return []

        # 1. BM25 Search
        bm25_results: List[Tuple[DocumentChunk, float]] = []
        if self.bm25 is not None:
            q_tokens = tokenize(query)
            if q_tokens:
                raw_scores = self.bm25.get_scores(q_tokens)
                for idx, score in enumerate(raw_scores):
                    chunk = self.chunks[idx]
                    if target_docs and chunk.filename not in target_docs and chunk.doc_id not in target_docs:
                        continue
                    if score > 0:
                        bm25_results.append((chunk, float(score)))
                bm25_results.sort(key=lambda x: x[1], reverse=True)

        # 2. Vector Search
        vector_results = self.vector_store.search(query, top_k=k * 2, target_docs=target_docs)

        # 3. Reciprocal Rank Fusion
        fused = self.reranker.reciprocal_rank_fusion(
            bm25_ranked=bm25_results[: k * 2],
            vector_ranked=vector_results,
            bm25_weight=self.bm25_weight,
            vector_weight=self.vector_weight,
            top_k=k,
        )

        return fused

    def rewrite_query(self, query: str, context_hint: Optional[str] = None) -> str:
        """Corrective query expansion for self-healing retrieval loops."""
        tokens = tokenize(query)
        expansion = []
        if "sla" in tokens or "uptime" in tokens:
            expansion.extend(["availability", "service credit", "penalty", "outage"])
        if "reimbursement" in tokens or "expense" in tokens:
            expansion.extend(["travel", "receipt", "forfeited", "submission", "per diem", "allowance"])
        if "refund" in tokens or "warranty" in tokens:
            expansion.extend(["return", "restocking", "deployment", "replacement"])
        if "termination" in tokens or "breach" in tokens:
            expansion.extend(["cause", "convenience", "notice period", "contract"])

        expanded = f"{query} {' '.join(expansion)}"
        if context_hint:
            expanded += f" {context_hint}"
        return expanded.strip()
