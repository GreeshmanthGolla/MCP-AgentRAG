"""Document RAG Worker: Executes hybrid retrieval and extracts evidence chunks."""
from __future__ import annotations

from typing import Any, Dict
from universal_copilot.config import settings
from universal_copilot.rag.hybrid_retriever import HybridRetriever
from universal_copilot.state import CaseState

_SHARED_RETRIEVER: HybridRetriever | None = None


def get_shared_retriever(force_reload: bool = False) -> HybridRetriever:
    global _SHARED_RETRIEVER
    if _SHARED_RETRIEVER is None or force_reload:
        _SHARED_RETRIEVER = HybridRetriever()
        docs_dir = settings().data_dir / "sample_docs"
        if docs_dir.exists():
            _SHARED_RETRIEVER.ingest_directory(docs_dir)
    elif len(_SHARED_RETRIEVER.chunks) == 0:
        docs_dir = settings().data_dir / "sample_docs"
        if docs_dir.exists() and list(docs_dir.glob("*.*")):
            _SHARED_RETRIEVER.ingest_directory(docs_dir)
    return _SHARED_RETRIEVER


def doc_rag_worker(state: CaseState) -> Dict[str, Any]:
    retriever = get_shared_retriever()
    query = state.get("query_rewrite") or state.get("sanitized_query") or state.get("raw_query") or ""
    target_docs = state.get("target_docs") or None

    chunks = retriever.retrieve(query=query, top_k=settings().retrieval.top_k, target_docs=target_docs)

    # Format findings summary
    findings_str = f"Retrieved {len(chunks)} chunks across {[c.filename for c in chunks]}."

    return {
        "retrieved_chunks": chunks,
        "query_rewrite": None,  # Clear consumed rewrite
        "route": "supervisor_node",
        "visited_nodes": ["doc_rag_worker"],
        "agent_scratchpad": [{
            "node": "doc_rag_worker",
            "thought": f"Executed hybrid retrieval for query: '{query}'",
            "findings": findings_str,
        }],
    }
