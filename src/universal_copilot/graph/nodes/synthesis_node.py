"""Synthesis Node: Drafts cited resolution response using assembled context."""
from __future__ import annotations

import re
from typing import Any, Dict, List
from universal_copilot.context.assembler import ContextAssembler
from universal_copilot.llm.provider import LLMProvider
from universal_copilot.schemas import Citation
from universal_copilot.state import CaseState


def synthesis_node(state: CaseState) -> Dict[str, Any]:
    assembler = ContextAssembler()
    llm = LLMProvider(
        mode=state.get("llm_mode"),
        model=state.get("llm_model"),
        api_key=state.get("llm_api_key"),
    )

    query = state.get("sanitized_query") or state.get("raw_query") or ""
    chunks = state.get("retrieved_chunks", [])
    entity_metadata = state.get("entity_metadata")
    scratchpad = state.get("agent_scratchpad", [])

    # Assemble isolated and pruned context
    context_prompt = assembler.assemble(
        query=query,
        entity_metadata=entity_metadata,
        chunks=chunks,
        scratchpad=scratchpad,
    )

    system_prompt = (
        "You are the Universal Resolution Copilot. Synthesize a professional, precise resolution draft "
        "addressing the user's inquiry based strictly on the retrieved document evidence. "
        "Every factual assertion MUST include an explicit bracketed citation in the form: [Doc: filename, Section: X] or [Doc: filename, Page: Y]."
    )

    response = llm.generate(prompt=context_prompt, system_prompt=system_prompt)
    draft_text = response.text

    # Extract bracketed citations from text
    citation_pattern = r"\[Doc:\s*([^,\]]+)(?:,\s*Section:\s*([^,\]]+))?(?:,\s*Page:\s*([^,\]]+))?\]"
    found_citations: List[Citation] = []

    for match in re.finditer(citation_pattern, draft_text):
        doc_name = match.group(1).strip()
        sec = match.group(2).strip() if match.group(2) else None
        page = int(match.group(3).strip()) if match.group(3) and match.group(3).strip().isdigit() else None

        # Quote snippet from chunk
        matching_chunk = next((c for c in chunks if c.filename == doc_name), None)
        quote = matching_chunk.content[:150] if matching_chunk else ""

        found_citations.append(
            Citation(
                claim=draft_text[:120],
                source_doc=doc_name,
                section=sec,
                page=page,
                quote=quote,
                chunk_id=matching_chunk.chunk_id if matching_chunk else None,
            )
        )

    return {
        "draft_response": draft_text,
        "citations": found_citations,
        "route": "critic_node",
        "tokens_used": state.get("tokens_used", 0) + response.prompt_tokens + response.completion_tokens,
        "visited_nodes": ["synthesis_node"],
        "agent_scratchpad": [{
            "node": "synthesis_node",
            "thought": "Synthesized draft response with source citations.",
            "findings": f"Generated {len(found_citations)} citations.",
        }],
    }
