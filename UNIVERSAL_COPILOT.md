# PROJECT SPECIFICATION & MASTER AGENT PROMPT: UNIVERSAL DOCUMENT & CASE RESOLUTION COPILOT

> **Instructions for Antigravity Agent**: 
> You are tasked with generating a production-grade, domain-independent **Universal Document & Case Resolution Copilot**. Follow this specification to build the complete repository with all source code, tests, documentation, evaluation harnesses, and synthetic data generators.

---

## 1. Project Overview & Objectives

Build a **governed, multi-agent AI copilot** that can ingest **any document or corpus** (PDF, DOCX, Markdown, TXT, CSV, JSON, Web content) along with **entity/database metadata**, autonomously analyze cases, execute verified tool actions, and generate **grounded, cited resolution drafts for human approval**.

### Core Architecture Principles
1. **Domain Independent**: Zero hardcoded domain rules. All domain intelligence is derived from ingested documents, dynamic entity context, and configurable policy YAMLs (`config/policies.yaml`).
2. **Strict Human Governance (HITL)**: The agent drafts and cites; it never auto-dispatches high-risk actions without explicit human approval.
3. **Multi-Agent Reflection & Grounding**: Dedicated Reflective Critic node cross-checks every claim in the generated draft against retrieved document chunks. If a claim lacks citation, it triggers an automatic corrective RAG loop.
4. **FastMCP Extensibility**: Connects to arbitrary external tools, databases, and APIs via Model Context Protocol (FastMCP) supporting `stdio`, `sse`, and `ws` transports.
5. **Dual Operation Mode**:
   - `LLM_MODE=offline`: Deterministic, zero-API-key simulation for CI/CD and offline verification.
   - `LLM_MODE=gemini` / `openai` / `ollama`: Live frontier LLM integration.

---

## 2. Target Directory & File Structure

Generate the complete project following this exact directory layout:

```text
universal-doc-copilot/
├── .env.example
├── .gitignore
├── Makefile
├── README.md
├── requirements.txt
├── run.py                          # Unified CLI entrypoint (demo, ask, serve-mcp, eval, web)
├── config/
│   ├── default_config.yaml
│   └── policies.yaml               # Configurable risk thresholds & escalation triggers
├── data/
│   ├── golden/
│   │   └── golden_set.jsonl        # Verified evaluation test cases
│   ├── sample_docs/
│   │   ├── company_policy.pdf
│   │   ├── vendor_contract.txt
│   │   └── api_spec.md
│   └── synthetic/
│       ├── entities.json           # Generic entity/user database
│       └── cases.json              # Historical sample cases
├── docs/
│   ├── architecture.md
│   ├── context-engineering.md
│   ├── evaluation-strategy.md
│   ├── fastmcp-integration.md
│   ├── memory-design.md
│   ├── owasp-llm-security.md
│   └── traceability-matrix.md
├── evals/
│   ├── baselines/
│   │   └── quality_baseline.json
│   ├── metrics.py                  # Faithfulness, citation recall, hallucination score
│   └── prompt_regression.py
├── scripts/
│   ├── generate_synthetic_data.py  # Self-contained seeded synthetic generator
│   └── run_benchmarks.py
├── src/
│   └── universal_copilot/
│       ├── __init__.py
│       ├── config.py
│       ├── state.py                # Generic CaseState, DocumentChunk, Citation
│       ├── schemas.py              # Pydantic boundary contracts
│       ├── cli.py
│       ├── context/                # Context engineering (Write, Select, Compress, Isolate)
│       │   ├── __init__.py
│       │   ├── assembler.py
│       │   ├── compression.py
│       │   ├── pruning.py
│       │   └── quarantine.py       # Isolated <untrusted_content> wrapper
│       ├── guardrails/             # PII redaction & prompt injection defense
│       │   ├── __init__.py
│       │   ├── injection_detector.py
│       │   └── pii_redactor.py
│       ├── ingestion/              # Multi-format document parser & chunker
│       │   ├── __init__.py
│       │   ├── loader.py           # PDF, DOCX, TXT, MD, CSV, JSON
│       │   └── chunker.py          # Semantic & sliding-window chunking
│       ├── rag/                    # Corrective Hybrid RAG
│       │   ├── __init__.py
│       │   ├── hybrid_retriever.py # BM25 + Cosine Dense Vector Search
│       │   ├── reranker.py
│       │   └── vector_store.py
│       ├── memory/                 # Tiered SQLite persistence
│       │   ├── __init__.py
│       │   ├── episodic.py         # Per-entity/case history
│       │   ├── semantic.py         # Long-term knowledge
│       │   ├── working.py          # Thread scratchpad
│       │   └── store.py
│       ├── mcp/                    # FastMCP Server & Client connectors
│       │   ├── __init__.py
│       │   ├── server.py           # FastMCP server exposing tools & resources
│       │   ├── client.py           # Multi-transport client (stdio, sse, ws)
│       │   ├── scopes.py           # Scope-based access control
│       │   └── tools/              # Dynamic tool handlers
│       ├── graph/                  # LangGraph Multi-Agent Orchestration
│       │   ├── __init__.py
│       │   ├── build.py            # Graph assembly & conditional edges
│       │   ├── runner.py
│       │   └── nodes/
│       │       ├── __init__.py
│       │       ├── guardrail_node.py
│       │       ├── triage_node.py
│       │       ├── supervisor_node.py
│       │       ├── doc_rag_worker.py
│       │       ├── entity_context_worker.py
│       │       ├── mcp_tool_worker.py
│       │       ├── escalation_node.py
│       │       ├── synthesis_node.py
│       │       ├── critic_node.py     # Reflective citation & grounding verifier
│       │       └── hitl_approval_node.py
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── provider.py         # Offline deterministic mock + Live Gemini/OpenAI
│       │   └── cache.py            # Sub-millisecond response & prompt hash cache
│       └── ui/
│           ├── __init__.py
│           └── streamlit_app.py    # Interactive web app with document uploader & HITL diff
└── tests/
    ├── conftest.py
    ├── test_guardrails.py
    ├── test_ingestion.py
    ├── test_rag_hybrid.py
    ├── test_multi_agent_graph.py
    ├── test_mcp_tools.py
    ├── test_memory_tiers.py
    ├── test_reflective_critic.py
    └── test_e2e_cases.py
```

---

## 3. Detailed Component Specifications

### 3.1. Dynamic State & Data Contracts (`state.py` & `schemas.py`)
* Define `DocumentChunk`:
  `chunk_id: str, doc_id: str, filename: str, page: Optional[int], section: Optional[str], content: str, score: float`.
* Define `Citation`:
  `claim: str, source_doc: str, section: Optional[str], page: Optional[int], quote: str`.
* Define `CaseState` (Typed LangGraph State):
  - `case_id: str`, `user_id: Optional[str]`, `raw_query: str`, `sanitized_query: str`
  - `entity_metadata: Dict[str, Any]` (generic entity attributes)
  - `retrieved_chunks: Annotated[List[DocumentChunk], operator.add]`
  - `citations: List[Citation]`
  - `agent_scratchpad: Annotated[List[Dict[str, Any]], operator.add]`
  - `draft_response: Optional[str]`
  - `is_grounded: bool`, `hallucination_score: float`
  - `requires_escalation: bool`, `escalation_reason: Optional[str]`
  - `human_approved: bool`, `final_response: Optional[str]`

### 3.2. Dynamic Ingestion & Hybrid RAG (`ingestion/` & `rag/`)
* **`loader.py`**: Auto-detects and extracts text + metadata from `.pdf`, `.docx`, `.txt`, `.md`, `.csv`, `.json`.
* **`chunker.py`**: Chunks content by structural boundaries (headings, double newlines) with configurable chunk size (500 tokens) and overlap (50 tokens).
* **`hybrid_retriever.py`**: Combines BM25 (`rank_bm25`) with Cosine Vector similarity (`all-MiniLM-L6-v2` or local hash-based embeddings for offline mode). Reciprocal Rank Fusion (RRF) merges results.

### 3.3. Multi-Agent Graph & Reflective Self-Healing (`graph/`)
Assemble a LangGraph state graph with the following node lifecycle:
1. `guardrail_node`: Checks prompt injection and masks PII. If injection is detected $\rightarrow$ route to `blocked_exit`.
2. `triage_node`: Analyzes intent and identifies required data sources.
3. `supervisor_node`: Coordinates worker dispatch:
   - Needs document facts $\rightarrow$ `doc_rag_worker`
   - Needs entity context $\rightarrow$ `entity_context_worker`
   - Needs external action/query $\rightarrow$ `mcp_tool_worker`
   - High risk/policy violation $\rightarrow$ `escalation_node`
4. `synthesis_node`: Synthesizes resolution draft with explicit bracketed citations `[Doc: filename, Page: X]`.
5. `critic_node`:
   - Checks every factual claim against `retrieved_chunks`.
   - If ungrounded or citations are missing $\rightarrow$ increments retry counter and loops back to `doc_rag_worker` with a targeted corrective query.
   - If grounded $\rightarrow$ routes to `hitl_approval_node`.
6. `hitl_approval_node`: Formats the draft with interactive diffs and source citations for human operator sign-off.

### 3.4. FastMCP Server & Client (`mcp/`)
* Create a standalone FastMCP server supporting `stdio`, `sse`, and `ws`.
* Expose tools:
  - `query_entity(entity_id: str)`: Fetch structured metadata.
  - `list_documents()`: Return catalog of ingested documents.
  - `execute_query(sql_or_search: str)`: Query structured/tabular records.
  - `log_audit_event(event_type: str, details: dict)`: Write compliance audit logs.
* Enforce scope validation (`read:docs`, `read:entity`, `write:audit`).

### 3.5. Multi-Tiered Memory (`memory/`)
* Implement SQLite-backed persistent memory:
  - **Working Memory**: Step-by-step scratchpad per active thread.
  - **Episodic Memory**: Scoped per `entity_id` / `case_id` storing historical interactions with LRU eviction.
  - **Semantic Memory**: Scoped for long-term document summaries and reference facts.

### 3.6. Interactive Streamlit UI (`ui/streamlit_app.py`)
* **Document Management Tab**: Drag-and-drop file uploader (PDF/DOCX/TXT) with instant chunking and index stats.
* **Case Resolution & Chat Tab**:
  - Entity selector & case query prompt.
  - Step-by-step agent execution trace (visualizing Supervisor $\rightarrow$ Worker $\rightarrow$ Critic flow).
  - Cited draft response with side-by-side source document excerpts.
  - **Human-in-the-Loop Review Panel**: "Approve & Send", "Edit Draft", or "Escalate".

---

## 4. Execution & Generation Steps for Antigravity

When executing this project generation, follow these steps sequentially:

1. **Scaffold Directory Structure & Dependencies**:
   - Create all directories as specified in Section 2.
   - Write `requirements.txt` (`langgraph`, `langchain-core`, `pydantic`, `fastmcp`, `rank_bm25`, `sentence-transformers`, `streamlit`, `pytest`, `sqlite3`).
2. **Generate Synthetic Data & Configs**:
   - Write `config/policies.yaml` and `config/default_config.yaml`.
   - Write `scripts/generate_synthetic_data.py` and execute it to populate `data/synthetic/` and `data/sample_docs/`.
3. **Implement Core Engine Modules**:
   - Implement `state.py`, `schemas.py`, `config.py`.
   - Implement `ingestion/` and `rag/` modules with hybrid search.
   - Implement `context/` and `guardrails/` modules.
   - Implement `memory/` SQLite persistence.
   - Implement `mcp/` FastMCP server and client adapters.
   - Implement `llm/` offline mock provider and live provider.
4. **Implement LangGraph Multi-Agent Nodes & Assembly**:
   - Build all nodes in `graph/nodes/`.
   - Connect graph in `graph/build.py` and `graph/runner.py`.
5. **Implement UI & CLI**:
   - Build `src/universal_copilot/ui/streamlit_app.py`.
   - Build `run.py` supporting `demo`, `ask`, `serve-mcp`, `eval`, and `web`.
6. **Implement Test Suite & Run Verification**:
   - Write complete pytest suites covering guardrails, ingestion, hybrid RAG, LangGraph multi-agent flow, critic self-healing loop, and FastMCP.
   - Run `pytest` to guarantee 100% test pass rate.
7. **Write Documentation**:
   - Populate all docs in `docs/` and create comprehensive `README.md`.

---

## 5. Quick Verification Commands

```bash
# 1. Install & Generate Synthetic Knowledge
pip install -r requirements.txt
python scripts/generate_synthetic_data.py

# 2. Run Deterministic Offline Test Suite
pytest -v

# 3. Run Sample Case Demo (Zero API key needed)
python run.py demo

# 4. Launch Interactive Web UI
python run.py web
```
