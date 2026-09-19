"""Document ingestion package for Universal Copilot.

Provides multi-format loading (PDF, DOCX, TXT, MD, CSV, JSON, HTML)
and structural boundary chunking.
"""

from universal_copilot.ingestion.loader import DocumentLoader, LoadedDocument
from universal_copilot.ingestion.chunker import DocumentChunker

__all__ = ["DocumentLoader", "LoadedDocument", "DocumentChunker"]
