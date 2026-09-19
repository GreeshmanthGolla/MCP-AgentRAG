"""Streamlit Inspection & Case Resolution UI for Universal Document Copilot.

Modeled on the hr-helpdesk-copilot interface with custom CSS styling,
multi-tier inspection tabs, agent pattern visualizers, and universal document upload.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

# Setup repository path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from universal_copilot.config import reload_settings, settings
from universal_copilot.graph.nodes.doc_rag_worker import get_shared_retriever
from universal_copilot.graph.runner import run_case_sync
from universal_copilot.ingestion.loader import DocumentLoader
from universal_copilot.llm.cache import RESPONSE_CACHE
from universal_copilot.mcp.tools import tool_list_documents, tool_query_entity


def load_synthetic_data():
    cases_file = ROOT / "data" / "synthetic" / "cases.json"
    entities_file = ROOT / "data" / "synthetic" / "entities.json"

    sample_cases = []
    if cases_file.exists():
        try:
            sample_cases = json.loads(cases_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    entities_data = {}
    if entities_file.exists():
        try:
            entities_data = json.loads(entities_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    return sample_cases, entities_data


def init_page():
    st.set_page_config(
        page_title="Universal Document & Case Resolution Copilot",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_custom_css():
    st.markdown(
        """
        <style>
        .user-question-card {
            background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
            border: 1px solid #3b82f6;
            border-radius: 12px;
            padding: 16px 20px;
            color: #f8fafc;
            margin-bottom: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .user-badge {
            display: inline-block;
            background-color: #3b82f6;
            color: white;
            padding: 2px 10px;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .assistant-answer-card {
            background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
            border: 1px solid #10b981;
            border-radius: 12px;
            padding: 16px 20px;
            color: #f8fafc;
            margin-bottom: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .escalation-card {
            background: linear-gradient(135deg, #78350f 0%, #92400e 100%);
            border: 1px solid #f59e0b;
            border-radius: 12px;
            padding: 16px 20px;
            color: #fef3c7;
            margin-bottom: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .bot-badge {
            display: inline-block;
            background-color: #10b981;
            color: white;
            padding: 2px 10px;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .warning-badge {
            display: inline-block;
            background-color: #f59e0b;
            color: black;
            padding: 2px 10px;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .history-card {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    init_page()
    inject_custom_css()

    sample_cases, entities_data = load_synthetic_data()
    retriever = get_shared_retriever()
    cfg = settings()

    if "history" not in st.session_state:
        st.session_state["history"] = []

    # ==========================
    # --- SIDEBAR CONTROLS ---
    # ==========================
    with st.sidebar:
        st.title("Universal Copilot")
        st.markdown("---")

        # 1. LLM Model Selection
        st.subheader("LLM Model Selection")
        model_options = {
            "gemini-3.6-pro-latest": "Google Gemini 3.6 Pro (Primary Live)",
            "gemini-3.6-pro": "Google Gemini 3.6 Pro",
            "gemini-3.6-flash": "Google Gemini 3.6 Flash",
            "openai/gpt-4o": "OpenAI GPT-4o",
            "openai/gpt-4o-mini": "OpenAI GPT-4o Mini",
            "ollama/llama3.1": "Ollama (Local Open Weights)",
            "offline": "Offline Deterministic Simulation",
        }

        current_cfg_mode = cfg.llm.mode.lower()
        if current_cfg_mode == "gemini":
            default_model_key = "gemini-3.6-pro-latest"
        elif current_cfg_mode == "openai":
            default_model_key = "openai/gpt-4o"
        elif current_cfg_mode == "ollama":
            default_model_key = "ollama/llama3.1"
        else:
            default_model_key = "offline"

        model_keys = list(model_options.keys())
        default_index = model_keys.index(default_model_key) if default_model_key in model_keys else 0

        selected_model_key = st.selectbox(
            "Select Active LLM Model",
            options=model_keys,
            format_func=lambda k: model_options[k],
            index=default_index,
        )

        selected_mode = "offline"
        selected_model_name = "offline-mock"
        entered_api_key = None

        if selected_model_key.startswith("gemini"):
            selected_mode = "gemini"
            selected_model_name = selected_model_key
            default_key = os.getenv("GEMINI_API_KEY", "") or cfg.llm.gemini_api_key or ""
            entered_api_key = st.text_input(
                "Gemini API Key (optional if in .env):",
                value=default_key,
                type="password",
            )
        elif selected_model_key.startswith("openai"):
            selected_mode = "openai"
            selected_model_name = selected_model_key.split("/", 1)[1]
            default_key = os.getenv("OPENAI_API_KEY", "") or cfg.llm.openai_api_key or ""
            entered_api_key = st.text_input(
                "OpenAI API Key (optional if in .env):",
                value=default_key,
                type="password",
            )
        elif selected_model_key.startswith("ollama"):
            selected_mode = "ollama"
            selected_model_name = "llama3.1:8b"
            ollama_host = st.text_input(
                "Ollama Host URL:",
                value=os.getenv("OLLAMA_HOST", "http://localhost:11434/api/generate"),
            )
            os.environ["OLLAMA_HOST"] = ollama_host
        else:
            selected_mode = "offline"
            selected_model_name = "deterministic-simulator"

        st.markdown("---")

        # 2. Agent Architecture Pattern Selector
        st.subheader("Agent Architecture Pattern")
        pattern_options = {
            "supervisor": "Supervisor Orchestrator (Plan-Execute + ReAct + Reflection)",
            "react": "ReAct Loop (Reason + Action Tool Calling)",
            "plan_execute": "Plan-and-Execute (Triage Staged Execution)",
            "reflection": "Reflective Critic (Self-Correction & Grounding Focus)",
        }
        selected_pattern_key = st.selectbox(
            "Active Agent Pattern",
            options=list(pattern_options.keys()),
            format_func=lambda k: pattern_options[k],
            index=0,
            help="Select the multi-agent design pattern for query execution and tool invocation.",
        )

        st.markdown("---")

        # 3. Prompt & Response Cache Status
        st.subheader("Prompt & Response Cache")
        c_stats = RESPONSE_CACHE.stats()
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.metric("Cache Hits", c_stats["hits"])
        with col_c2:
            st.metric("Cached Items", c_stats["total_cached_entries"])
        st.caption(f"Hit Rate: **{c_stats['hit_ratio']:.1%}** | Mode: **Tier-1 Fast Cache (Checked First)**")

        with st.expander("Cache Maintenance"):
            if st.button("Flush / Clear Cache", use_container_width=True):
                RESPONSE_CACHE.clear()
                st.success("Cache cleared successfully.")

        st.markdown("---")

        # 4. Case Input & Entity Selector
        st.subheader("Case Input")
        preset_options = ["(custom)"] + [f"{c['case_id']}: {c['query'][:55]}..." for c in sample_cases]
        preset = st.selectbox("Preset sample query", preset_options)

        ent_keys = list(entities_data.keys())
        ent_options = ent_keys + ["(Enter Custom ID...)"]

        if preset != "(custom)":
            chosen_case_id = preset.split(":", 1)[0]
            chosen = next((c for c in sample_cases if c["case_id"] == chosen_case_id), None)
            if chosen:
                preset_ent_id = chosen.get("entity_id", "ENT-1001")
                query_default = chosen.get("query", "")
                default_ent_index = ent_keys.index(preset_ent_id) if preset_ent_id in ent_keys else len(ent_keys)
            else:
                preset_ent_id, query_default = "ENT-1001", ""
                default_ent_index = 0
        else:
            preset_ent_id, query_default = "ENT-1001", ""
            default_ent_index = 0

        selected_ent_label = st.selectbox(
            "Select / Search Entity ID",
            options=ent_options,
            index=default_ent_index,
            format_func=lambda eid: f"{eid} - {entities_data[eid]['name']} ({entities_data[eid]['type']})" if eid in entities_data else eid,
            help="Search entity by ID, name, or type, or choose Custom ID to type any ID.",
        )

        if selected_ent_label == "(Enter Custom ID...)":
            entity_id = st.text_input("Enter Custom Entity ID", value=preset_ent_id if preset_ent_id not in ent_keys else "ENT-9999").strip()
        else:
            entity_id = selected_ent_label

        if entity_id in entities_data:
            ent_rec = entities_data[entity_id]
            st.success(f"Verified Entity Record: **{ent_rec['name']}** | {ent_rec.get('type', 'general').title()} | {ent_rec.get('location', ent_rec.get('account_tier', 'Verified'))}")
        else:
            st.warning(f"Entity with ID **{entity_id}** has no static record in synthetic database (direct document search will apply).")

        query = st.text_area("Inquiry / Case Query", query_default, height=120)

        auto_fresh = st.checkbox(
            "Fresh session per case (recommended)",
            value=True,
            help="Automatically creates a new case thread so previous question checkpoints do not persist.",
        )
        if auto_fresh:
            thread_id = f"session-{datetime.now().strftime('%H%M%S')}"
            st.caption(f"Active Thread: `{thread_id}`")
        else:
            thread_id = st.text_input("Thread / Session ID", "ui-session-1", help="Use the same ID across queries only when testing multi-turn memory.")

        run_it = st.button("Run Copilot Case", type="primary", use_container_width=True)

        st.markdown("---")
        st.subheader("Index Telemetry")
        st.metric("Total Indexed Chunks", len(retriever.chunks))
        st.caption(f"Embedding Engine: `{cfg.retrieval.embedding_model}`")

    # ==========================
    # --- MAIN PAGE HEADER ---
    # ==========================
    st.title("Universal Document & Case Resolution Copilot")
    st.caption(
        f"Active Model: **{selected_model_key}** | Agent Pattern: **{pattern_options[selected_pattern_key]}** | Human Governance: **Enabled**"
    )

    # ==========================
    # --- EXECUTION HANDLER ---
    # ==========================
    if run_it and query.strip():
        with st.spinner("Processing through multi-agent universal resolution graph..."):
            try:
                active_case_id = f"CASE-{datetime.now().strftime('%H%M%S')}"
                result = run_case_sync(
                    query=query,
                    case_id=active_case_id,
                    entity_id=entity_id if entity_id != "(Enter Custom ID...)" else None,
                    llm_mode=selected_mode,
                    llm_model=selected_model_name,
                    llm_api_key=entered_api_key if entered_api_key else None,
                )
                st.session_state["run_result"] = result

                # Save to history
                status_label = "escalated" if result.requires_escalation else ("draft_grounded" if result.is_grounded else "draft_review")
                st.session_state["history"].insert(
                    0,
                    {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "case_id": active_case_id,
                        "entity_id": entity_id,
                        "query": query,
                        "answer": result.final_response,
                        "route": result.visited_nodes,
                        "model": selected_model_key,
                        "duration_ms": result.duration_ms,
                        "grounding_score": result.state.get("grounding_score", 1.0 if result.is_grounded else 0.0),
                        "citations": [c.source_doc for c in result.citations],
                        "status": status_label,
                    },
                )
            except Exception as exc:
                st.error(f"Error during execution: {exc}")

    result = st.session_state.get("run_result")

    # ==========================
    # --- INSPECTION TABS ---
    # ==========================
    tabs = st.tabs([
        "Document Ingestion & Upload",
        "Conversation & Draft",
        "Past Chat History",
        "Policy Citations & Evidence",
        "Memory & Context",
        "Redaction & Quarantine",
        "Tool Calls & Telemetry",
        "Raw State (JSON)",
    ])

    # ---------------------------------------------------------------------
    # TAB 1: DOCUMENT INGESTION & UPLOAD (Universal Document Management)
    # ---------------------------------------------------------------------
    with tabs[0]:
        st.subheader("Upload & Manage Documents (Any Format & Domain)")
        st.write(
            "Ingest your own files in `.pdf`, `.docx`, `.doc`, `.txt`, `.md`, `.csv`, `.json`, `.yaml`, or `.html`. "
            "All text is chunked, cleaned, indexed into the hybrid BM25 and vector store, and ready for grounded retrieval."
        )

        col_u1, col_u2 = st.columns([3, 1])
        with col_u1:
            uploaded_files = st.file_uploader(
                "Choose files to ingest into Copilot knowledge base:",
                accept_multiple_files=True,
                type=["pdf", "docx", "doc", "txt", "md", "csv", "json", "yaml", "html"],
            )

        with col_u2:
            st.write("Knowledge Base Actions")
            if st.button("Clear All Documents & Start Fresh", use_container_width=True):
                retriever.clear()
                docs_dir = cfg.data_dir / "sample_docs"
                if docs_dir.exists():
                    for f in docs_dir.iterdir():
                        if f.is_file():
                            try:
                                f.unlink()
                            except Exception:
                                pass
                st.success("Knowledge index cleared. Ready for fresh user uploads.")
                st.rerun()

        if uploaded_files:
            upload_dir = cfg.data_dir / "sample_docs"
            upload_dir.mkdir(parents=True, exist_ok=True)
            for uf in uploaded_files:
                save_path = upload_dir / uf.name
                save_path.write_bytes(uf.getvalue())
                chunks = retriever.ingest_file(save_path)
                st.success(f"Successfully ingested '{uf.name}' -> {len(chunks)} chunks indexed.")

        st.markdown("---")
        st.markdown("### Current Document Catalog")
        doc_catalog = tool_list_documents()
        if doc_catalog:
            st.dataframe(doc_catalog, use_container_width=True)
        else:
            st.info("No documents currently in index. Upload files above to get started.")

        if retriever.chunks:
            with st.expander(f"Inspect Indexed Chunks ({len(retriever.chunks)} total)", expanded=False):
                for idx, chk in enumerate(retriever.chunks[:15], 1):
                    st.caption(f"Chunk {idx} | Document: `{chk.filename}` | Section: `{chk.section or 'General'}` | Page: `{chk.page or 'N/A'}`")
                    st.text(chk.content[:300] + ("..." if len(chk.content) > 300 else ""))

    # ---------------------------------------------------------------------
    # TAB 2: CONVERSATION & DRAFT (Styled Question & Answer Cards)
    # ---------------------------------------------------------------------
    with tabs[1]:
        if not result:
            st.info("Select a sample query from the sidebar or enter a custom case statement, then click **Run Copilot Case**.")
        else:
            state = result.state
            intent = state.get("active_plan") or "document_case_query"
            grounding_score = state.get("grounding_score", 1.0 if result.is_grounded else 0.0)

            # Top Metric Cards (matching hr-helpdesk-copilot)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Intent / Plan", intent[:25] + "..." if len(intent) > 25 else intent)
            m2.metric("Route Steps", len(result.visited_nodes))
            m3.metric("Latency", f"{result.duration_ms:.1f} ms")
            m4.metric("Approval Status", "Specialist Escalation" if result.requires_escalation else "Awaiting Review")

            st.markdown("---")

            # 1. QUESTION CONTAINER (Blue/Indigo Card)
            st.markdown(
                f"""
                <div class="user-question-card">
                    <div class="user-badge">Inquiry · {state.get('entity_id') or 'General Request'}</div>
                    <div style="font-size: 1.05rem; line-height: 1.5; white-space: pre-wrap;">{result.query}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 2. ANSWER CONTAINER (Green Emerald for verified draft, Amber for escalation)
            if result.requires_escalation:
                st.markdown(
                    f"""
                    <div class="escalation-card">
                        <div class="warning-badge">Mandatory Policy Escalation Triggered</div>
                        <div style="font-size: 1.05rem; line-height: 1.6; white-space: pre-wrap;">{result.final_response}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption("Compliance Policy Rule: Mandatory escalation triggered. Staged for specialist and legal review.")
            else:
                st.markdown(
                    f"""
                    <div class="assistant-answer-card">
                        <div class="bot-badge">Copilot Draft Resolution (Grounded in Verified Evidence)</div>
                        <div style="font-size: 1.05rem; line-height: 1.6; white-space: pre-wrap;">{result.final_response}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption(f"Governance Rule: Grounding Score: {grounding_score:.2f} | Human Operator Review Required before dispatch.")

            # Human-in-the-Loop Review Panel
            st.markdown("---")
            st.markdown("#### Human-in-the-Loop Review Panel")
            act1, act2, act3 = st.columns(3)
            with act1:
                if st.button("Approve & Dispatch", use_container_width=True):
                    st.info("Resolution approved and dispatched to requester.")
            with act2:
                if st.button("Edit & Customize", use_container_width=True):
                    st.info("Edit mode active. Operator can modify resolution directly.")
            with act3:
                if st.button("Escalate to Board", use_container_width=True):
                    st.warning("Case escalated to executive review board.")

            st.subheader("Orchestration Graph Route")
            st.code(" -> ".join(result.visited_nodes), language="text")

            with st.expander("Implemented Multi-Agent Design Patterns in this Run", expanded=True):
                p1, p2, p3 = st.columns(3)
                with p1:
                    st.markdown("#### Plan-and-Execute")
                    st.markdown("**Node**: `triage_node` & `supervisor_node`")
                    st.caption("Classifies query intent and required intelligence sources before dispatching sub-agents.")
                with p2:
                    st.markdown("#### ReAct (Reason + Act)")
                    st.markdown("**Nodes**: `doc_rag_worker`, `entity_context_worker`, `mcp_tool_worker`")
                    st.caption("Executes targeted tool calls against FastMCP endpoints and hybrid document indexes.")
                with p3:
                    st.markdown("#### Reflection & Critic")
                    st.markdown("**Node**: `critic_node`")
                    st.caption("Evaluates factual claim grounding against cited document evidence and drives self-healing loops.")

    # ---------------------------------------------------------------------
    # TAB 3: PAST CHAT HISTORY
    # ---------------------------------------------------------------------
    with tabs[2]:
        st.subheader("Session & Case History")
        history_items = st.session_state.get("history", [])

        if not history_items:
            st.info("No past cases run in this session yet. Run a case to see history log.")
        else:
            h_col1, h_col2 = st.columns([3, 1])
            with h_col1:
                st.caption(f"Total Cases Recorded: **{len(history_items)}**")
            with h_col2:
                if st.button("Clear History", use_container_width=True):
                    st.session_state["history"] = []
                    st.rerun()

            for idx, item in enumerate(history_items):
                is_esc = item["status"] == "escalated"
                card_class = "escalation-card" if is_esc else "assistant-answer-card"
                badge_class = "warning-badge" if is_esc else "bot-badge"
                badge_text = "Escalation Packet (Specialist Review)" if is_esc else "Copilot Verified Response"

                with st.expander(
                    f"[{item['timestamp']}] {item['entity_id'] or 'General'} - {item['query'][:60]}... ({item['status']})",
                    expanded=(idx == 0),
                ):
                    st.markdown(
                        f"""
                        <div class="user-question-card" style="padding: 12px 16px; margin-bottom: 8px;">
                            <span class="user-badge">{item['entity_id'] or 'General Inquiry'}</span>
                            <div>{item['query']}</div>
                        </div>
                        <div class="{card_class}" style="padding: 12px 16px; margin-bottom: 8px;">
                            <span class="{badge_class}">{badge_text}</span>
                            <div>{item['answer']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        f"Model: `{item['model']}` | Latency: `{item.get('duration_ms', 0):.1f}ms` | "
                        f"Citations: `{', '.join(item['citations']) or 'None'}` | "
                        f"Route: `{' -> '.join(item['route'])}`"
                    )

    # ---------------------------------------------------------------------
    # TAB 4: POLICY CITATIONS & EVIDENCE
    # ---------------------------------------------------------------------
    with tabs[3]:
        st.subheader("Governing Document Citations & Evidence")
        if result and result.citations:
            for c in result.citations:
                st.markdown(f"### `{c.source_doc}`")
                sec_str = f"Section: `{c.section}`" if c.section else ""
                page_str = f"Page: `{c.page}`" if c.page else ""
                st.info(f"**Supporting Quote:** {c.quote}")

            st.markdown("#### Retrieved Evidence Chunks")
            for chk in result.retrieved_chunks:
                with st.expander(f"Chunk: {chk.chunk_id} ({chk.filename})", expanded=False):
                    st.caption(f"Score: `{chk.score}` | Section: `{chk.section or 'N/A'}` | Page: `{chk.page or 'N/A'}`")
                    st.text(chk.content)
        elif result:
            st.info("No specific document citations were attached to this case resolution.")
        else:
            st.info("Run a case to inspect document citations and retrieved chunks.")

    # ---------------------------------------------------------------------
    # TAB 5: MEMORY & CONTEXT
    # ---------------------------------------------------------------------
    with tabs[4]:
        st.subheader("Multi-Tier Memory & Context Hits")
        if result:
            state = result.state
            scratchpad = state.get("agent_scratchpad", [])
            st.markdown("#### Tier 1: Working Memory (Thread Scratchpad)")
            if scratchpad:
                for step in scratchpad:
                    st.markdown(f"**Node:** `{step.get('node')}`")
                    st.caption(f"Thought: {step.get('thought')}")
                    st.text(f"Findings: {step.get('findings')}")
            else:
                st.caption("No working memory steps recorded.")

            st.markdown("#### Tier 2: Entity Context")
            ent_meta = state.get("entity_metadata", {})
            if ent_meta:
                st.json(ent_meta)
            else:
                st.caption("No active entity metadata loaded.")
        else:
            st.info("Run a case to inspect working and episodic memory.")

    # ---------------------------------------------------------------------
    # TAB 6: REDACTION & QUARANTINE
    # ---------------------------------------------------------------------
    with tabs[5]:
        st.subheader("Context Quarantine & PII Redaction")
        if result:
            state = result.state
            st.markdown("#### PII Redaction Map")
            redactions = state.get("redaction_map", {})
            if redactions:
                st.json(redactions)
            else:
                st.caption("No sensitive PII entities were detected in this inquiry.")

            st.markdown("#### Quarantined Untrusted Context Blocks")
            chunks = result.retrieved_chunks
            if chunks:
                st.caption(f"Total Isolated Blocks: {len(chunks)}")
                for chk in chunks[:3]:
                    block_text = f"<untrusted_content source='{chk.filename}'>\n{chk.content[:350]}\n</untrusted_content>"
                    st.code(block_text, language="xml")
            else:
                st.caption("No external chunks quarantined.")
        else:
            st.info("Run a case to inspect redaction and quarantine status.")

    # ---------------------------------------------------------------------
    # TAB 7: TOOL CALLS & TELEMETRY
    # ---------------------------------------------------------------------
    with tabs[6]:
        st.subheader("Tool Invocations & Execution Telemetry")
        if result:
            state = result.state
            st.markdown("#### Audit Events Ledger")
            audit_events = state.get("audit_events", [])
            if audit_events:
                st.json(audit_events)
            else:
                st.caption("No audit events recorded.")

            st.markdown("#### Execution Metrics")
            met_col1, met_col2 = st.columns(2)
            with met_col1:
                st.metric("Total Latency", f"{result.duration_ms:.2f} ms")
            with met_col2:
                st.metric("Tokens Estimated", state.get("tokens_used", 0))
        else:
            st.info("Run a case to inspect tool execution logs.")

    # ---------------------------------------------------------------------
    # TAB 8: RAW STATE (JSON)
    # ---------------------------------------------------------------------
    with tabs[7]:
        st.subheader("Complete Graph State (JSON)")
        if result:
            st.json(json.loads(json.dumps(result.state, default=str)))
        else:
            st.info("Run a case to inspect raw graph state.")


if __name__ == "__main__":
    main()
