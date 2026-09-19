"""Reciprocal Rank Fusion (RRF) and relevance reranker."""
from __future__ import annotations

from typing import Dict, List, Tuple
from universal_copilot.schemas import DocumentChunk


class Reranker:
    """Combines BM25 and Dense Vector search results using Reciprocal Rank Fusion."""

    def __init__(self, rrf_k: int = 60, relevance_floor: float = 0.001):
        self.rrf_k = rrf_k
        self.relevance_floor = relevance_floor

    def reciprocal_rank_fusion(
        self,
        bm25_ranked: List[Tuple[DocumentChunk, float]],
        vector_ranked: List[Tuple[DocumentChunk, float]],
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
        top_k: int = 5,
    ) -> List[DocumentChunk]:
        """Merges ranked lists using weighted reciprocal rank fusion."""
        scores: Dict[str, float] = {}
        chunk_map: Dict[str, DocumentChunk] = {}

        # Process BM25 rankings
        for rank, (chunk, _) in enumerate(bm25_ranked):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_val = bm25_weight / (self.rrf_k + rank + 1)
            scores[cid] = scores.get(cid, 0.0) + rrf_val

        # Process Vector rankings
        for rank, (chunk, _) in enumerate(vector_ranked):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_val = vector_weight / (self.rrf_k + rank + 1)
            scores[cid] = scores.get(cid, 0.0) + rrf_val

        # Sort by merged RRF score
        sorted_cids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results: List[DocumentChunk] = []
        for cid, score in sorted_cids:
            if score >= self.relevance_floor:
                c = chunk_map[cid]
                # Update chunk score with fused score
                c.score = round(score, 4)
                results.append(c)
            if len(results) >= top_k:
                break

        return results
