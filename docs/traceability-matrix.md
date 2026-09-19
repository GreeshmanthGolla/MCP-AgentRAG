# Requirements Traceability Matrix (RTM)

## 1. Specification Mapping

This matrix verifies that every functional requirement, architecture principle, and component from [UNIVERSAL_COPILOT.md](file:///c:/Users/GREESHMANTH/Desktop/Agentic-RAG/UNIVERSAL_COPILOT.md) is implemented and validated by automated tests.

| Requirement / ID | Specification Description | Implementing Module | Verification Test | Status |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-01: Domain Independence** | Zero hardcoded domain rules; derived from docs, entity metadata, and policy YAML. | `config/policies.yaml`, `config.py`, `loader.py` | `tests/test_e2e_cases.py` | [VERIFIED] |
| **REQ-02: Multi-Format Ingestion** | Ingest PDF, DOCX, TXT, MD, CSV, JSON, HTML with page/section preservation. | `src/universal_copilot/ingestion/loader.py`, `chunker.py` | `tests/test_ingestion.py` | [VERIFIED] |
| **REQ-03: Corrective Hybrid RAG** | BM25 + Cosine Dense Vector search fused with Reciprocal Rank Fusion (RRF). | `src/universal_copilot/rag/hybrid_retriever.py`, `reranker.py` | `tests/test_rag_hybrid.py` | [VERIFIED] |
| **REQ-04: Multi-Agent Graph** | LangGraph supervisor + specialist workers with conditional routing. | `src/universal_copilot/graph/build.py`, `nodes/` | `tests/test_multi_agent_graph.py` | [VERIFIED] |
| **REQ-05: Reflective Critic** | Self-healing corrective loop checking grounding and citations against retrieved chunks. | `src/universal_copilot/graph/nodes/critic_node.py` | `tests/test_reflective_critic.py` | [VERIFIED] |
| **REQ-06: Strict HITL Governance** | The agent drafts and cites; high-risk actions mandate human review. | `src/universal_copilot/graph/nodes/hitl_approval_node.py` | `tests/test_e2e_cases.py` | [VERIFIED] |
| **REQ-07: FastMCP Extensibility** | FastMCP server & client exposing tools with scope validation (`read:docs`, etc.). | `src/universal_copilot/mcp/server.py`, `client.py`, `scopes.py` | `tests/test_mcp_tools.py` | [VERIFIED] |
| **REQ-08: Multi-Tiered Memory** | SQLite-backed Working, Episodic (LRU), and Semantic memory persistence. | `src/universal_copilot/memory/store.py`, `working.py`, `episodic.py`, `semantic.py` | `tests/test_memory_tiers.py` | [VERIFIED] |
| **REQ-09: Dual Operation Mode** | Deterministic `offline` mode for CI/evals + Live `gemini` / `openai`. | `src/universal_copilot/llm/provider.py`, `cache.py` | `evals/prompt_regression.py` | [VERIFIED] |
| **REQ-10: OWASP LLM Defense** | Prompt injection scanner and reversible PII redaction. | `src/universal_copilot/guardrails/injection_detector.py`, `pii_redactor.py` | `tests/test_guardrails.py` | [VERIFIED] |
| **REQ-11: Interactive Streamlit UI** | Multi-tab UI for document upload, trace inspection, and HITL review. | `src/universal_copilot/ui/streamlit_app.py` | `python run.py web` | [VERIFIED] |
| **REQ-12: Unified CLI Entrypoint** | Unified CLI supporting `demo`, `ask`, `serve-mcp`, `eval`, `web`. | `run.py`, `src/universal_copilot/cli.py` | `python run.py demo` | [VERIFIED] |
