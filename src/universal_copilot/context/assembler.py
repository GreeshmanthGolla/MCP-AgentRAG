"""Context Assembler: Implements Write, Select, Compress, Isolate."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from universal_copilot.context.compression import ContextCompressor
from universal_copilot.context.pruning import prune_redundant_lines, truncate_to_token_budget
from universal_copilot.context.quarantine import quarantine_content
from universal_copilot.schemas import DocumentChunk


class ContextAssembler:
    """Assembles prompt context under strict token budgets and isolation boundaries."""

    def __init__(self, max_context_tokens: int = 3000):
        self.max_tokens = max_context_tokens
        self.compressor = ContextCompressor()

    def assemble(
        self,
        query: str,
        entity_metadata: Optional[Dict[str, Any]] = None,
        chunks: Optional[List[DocumentChunk]] = None,
        scratchpad: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        sections = []

        # 1. Entity Metadata Context
        if entity_metadata:
            clean_entity = {k: v for k, v in entity_metadata.items() if k != "history"}
            if "history" in entity_metadata:
                clean_entity["recent_history"] = self.compressor.compress_history(
                    entity_metadata.get("history", [])
                )
            entity_json = json.dumps(clean_entity, indent=2)
            sections.append(f"### ENTITY CONTEXT (VERIFIED RECORD)\n{entity_json}")

        # 2. Agent Scratchpad / Working Memory
        if scratchpad:
            scratch_lines = []
            for step in scratchpad[-4:]:
                node = step.get("node", "step")
                thought = step.get("thought", "")
                findings = step.get("findings", "")
                scratch_lines.append(f"- [{node}]: {thought} {findings}".strip())
            if scratch_lines:
                sections.append(f"### AGENT SCRATCHPAD\n" + "\n".join(scratch_lines))

        # 3. Retrieved Knowledge Evidence (Quarantined)
        if chunks:
            chunk_sections = []
            for idx, c in enumerate(chunks, 1):
                ref = c.to_citation_reference()
                compressed_body = self.compressor.compress_chunk(c, max_chars=800)
                quarantined_body = quarantine_content(compressed_body, source_tag=f"evidence_{idx}")
                chunk_sections.append(f"Source {idx}: {ref}\n{quarantined_body}")

            evidence_text = "\n\n".join(chunk_sections)
            sections.append(f"### RETRIEVED DOCUMENT EVIDENCE\n{evidence_text}")

        # 4. User Case Query (Quarantined)
        quarantined_query = quarantine_content(query, source_tag="user_case_query")
        sections.append(f"### ACTIVE CASE QUERY\n{quarantined_query}")

        full_context = "\n\n".join(sections)
        full_context = prune_redundant_lines(full_context)
        return truncate_to_token_budget(full_context, max_tokens=self.max_tokens)
