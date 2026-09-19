"""Tests for Hybrid RAG: BM25, Vector Search, and RRF Fusion."""
from __future__ import annotations

import pytest
from universal_copilot.rag.hybrid_retriever import HybridRetriever
from universal_copilot.rag.reranker import Reranker
from universal_copilot.rag.vector_store import InMemoryVectorStore, cosine_similarity
from universal_copilot.schemas import DocumentChunk


def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]

    assert pytest.approx(cosine_similarity(v1, v2), 0.001) == 1.0
    assert pytest.approx(cosine_similarity(v1, v3), 0.001) == 0.0


def test_reranker_rrf():
    reranker = Reranker(rrf_k=60, relevance_floor=0.001)

    c1 = DocumentChunk(doc_id="d1", filename="doc1.txt", content="Uptime SLA is 99.95%")
    c2 = DocumentChunk(doc_id="d2", filename="doc2.txt", content="Reimbursement window is 30 days")

    bm25_ranked = [(c1, 10.5), (c2, 4.2)]
    vector_ranked = [(c1, 0.92), (c2, 0.55)]

    fused = reranker.reciprocal_rank_fusion(bm25_ranked, vector_ranked, top_k=2)
    assert len(fused) == 2
    assert fused[0].chunk_id == c1.chunk_id
    assert fused[0].score > fused[1].score


def test_hybrid_retriever(retriever):
    # Query for SLA
    hits = retriever.retrieve("What is the monthly uptime guarantee for core APIs?", top_k=3)
    assert len(hits) > 0
    contents = " ".join([h.content for h in hits])
    assert "99.95%" in contents or "availability" in contents.lower()
