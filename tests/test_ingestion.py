"""Tests for multi-format document loading and structural chunking."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from universal_copilot.ingestion.chunker import DocumentChunker
from universal_copilot.ingestion.loader import DocumentLoader, LoadedDocument


def test_loader_txt_and_md(tmp_path):
    loader = DocumentLoader()

    # TXT test
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Hello World. This is a test plain text document.", encoding="utf-8")
    doc_txt = loader.load(txt_file)
    assert doc_txt.filename == "test.txt"
    assert "Hello World" in doc_txt.raw_content

    # MD test
    md_file = tmp_path / "spec.md"
    md_file.write_text("# Title\n\nSome body text\n\n---\n\n# Page 2\n\nSecond page text.", encoding="utf-8")
    doc_md = loader.load(md_file)
    assert len(doc_md.pages) >= 2


def test_loader_csv_and_json(tmp_path):
    loader = DocumentLoader()

    # CSV test
    csv_file = tmp_path / "records.csv"
    csv_file.write_text("id,name,role\n1,Alice,Admin\n2,Bob,User\n", encoding="utf-8")
    doc_csv = loader.load(csv_file)
    assert "Headers: id, name, role" in doc_csv.raw_content
    assert "Alice" in doc_csv.raw_content

    # JSON test
    json_file = tmp_path / "data.json"
    data = {"company": "Acme", "tier": "Gold", "active": True}
    json_file.write_text(json.dumps(data), encoding="utf-8")
    doc_json = loader.load(json_file)
    assert "Acme" in doc_json.raw_content


def test_chunker_semantic_boundaries():
    chunker = DocumentChunker(chunk_size_tokens=100, chunk_overlap_tokens=20)
    raw_text = """SECTION 1: OVERVIEW
This is the initial overview section discussing corporate terms.

SECTION 2: PAYMENT RULES
Invoices must be submitted on time. Late payments incur interest charges.

SECTION 3: TERMINATION
Termination requires written notice of 30 days.
"""
    doc = LoadedDocument(
        doc_id="doc-test-1",
        filename="test_policy.txt",
        file_type="txt",
        raw_content=raw_text,
        pages=[(1, raw_text)],
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 3
    sections = [c.section for c in chunks if c.section]
    assert any("SECTION 1" in s for s in sections)
    assert any("SECTION 2" in s for s in sections)
    assert any("SECTION 3" in s for s in sections)
