"""Structural boundary and sliding-window chunker."""
from __future__ import annotations

import re
from typing import List, Optional
from universal_copilot.config import settings
from universal_copilot.ingestion.loader import LoadedDocument
from universal_copilot.schemas import DocumentChunk


class DocumentChunker:
    """Chunks documents using semantic boundaries (headings, sections) and token constraints."""

    def __init__(
        self,
        chunk_size_tokens: Optional[int] = None,
        chunk_overlap_tokens: Optional[int] = None,
    ):
        s = settings().chunking
        self.chunk_size = chunk_size_tokens or s.chunk_size_tokens
        self.chunk_overlap = chunk_overlap_tokens or s.chunk_overlap_tokens
        # 1 token ~ 4 characters heuristic
        self.max_chars = self.chunk_size * 4
        self.overlap_chars = self.chunk_overlap * 4

    def chunk_document(self, doc: LoadedDocument) -> List[DocumentChunk]:
        all_chunks: List[DocumentChunk] = []

        # If document has distinct pages, chunk per page while preserving coordinates
        for page_num, page_text in doc.pages:
            chunks = self._chunk_page(doc, page_num, page_text)
            all_chunks.extend(chunks)

        # Fallback if no page chunks generated
        if not all_chunks and doc.raw_content.strip():
            all_chunks = self._chunk_page(doc, page_num=1, page_text=doc.raw_content)

        return all_chunks

    def _chunk_page(self, doc: LoadedDocument, page_num: int, text: str) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []

        # Split on structural boundaries: headings or double newlines
        # Matches markdown headings (#, ##, ###) or SECTION N:
        boundary_pattern = r"(?=(\n(?:#+\s+|SECTION\s+\d+|ARTICLE\s+\d+|CLAUSE\s+\d+)))"
        sections = re.split(boundary_pattern, text, flags=re.IGNORECASE)

        # Merge split components
        merged_sections: List[str] = []
        current_sec = ""
        for part in sections:
            if not part:
                continue
            if re.match(r"^\n(?:#+\s+|SECTION\s+\d+|ARTICLE\s+\d+|CLAUSE\s+\d+)", part, re.IGNORECASE):
                if current_sec.strip():
                    merged_sections.append(current_sec.strip())
                current_sec = part
            else:
                current_sec += part
        if current_sec.strip():
            merged_sections.append(current_sec.strip())

        if not merged_sections:
            merged_sections = [p.strip() for p in text.split("\n\n") if p.strip()] or [text.strip()]

        current_heading = None
        for sec in merged_sections:
            # Detect section title
            heading_match = re.search(r"^(?:#+\s+|SECTION\s+[\w\.\-]+:?|ARTICLE\s+[\w\.\-]+:?)\s*([^\n]+)", sec, re.IGNORECASE)
            if heading_match:
                current_heading = heading_match.group(0).strip("# \t\r\n")

            # Check if section fits within max_chars
            if len(sec) <= self.max_chars:
                chunks.append(
                    DocumentChunk(
                        doc_id=doc.doc_id,
                        filename=doc.filename,
                        page=page_num,
                        section=current_heading,
                        content=sec,
                        metadata={"file_type": doc.file_type},
                    )
                )
            else:
                # Sub-chunk using sliding window with overlap
                sub_chunks = self._sliding_window(sec, current_heading, doc, page_num)
                chunks.extend(sub_chunks)

        return chunks

    def _sliding_window(
        self, text: str, heading: Optional[str], doc: LoadedDocument, page_num: int
    ) -> List[DocumentChunk]:
        results: List[DocumentChunk] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.max_chars, text_len)
            # Try to break on newline or period near the end
            if end < text_len:
                cut = text.rfind("\n", start, end)
                if cut == -1 or cut <= start:
                    cut = text.rfind(". ", start, end)
                if cut > start:
                    end = cut + 1

            chunk_content = text[start:end].strip()
            if chunk_content:
                results.append(
                    DocumentChunk(
                        doc_id=doc.doc_id,
                        filename=doc.filename,
                        page=page_num,
                        section=heading,
                        content=chunk_content,
                        metadata={"file_type": doc.file_type},
                    )
                )

            if end >= text_len:
                break
            start = max(start + 1, end - self.overlap_chars)

        return results
