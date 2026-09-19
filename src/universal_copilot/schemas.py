"""Pydantic boundary schemas and contracts for Universal Document Copilot."""
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: f"chk_{uuid.uuid4().hex[:8]}")
    doc_id: str
    filename: str
    page: Optional[int] = None
    section: Optional[str] = None
    content: str
    score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_citation_reference(self) -> str:
        loc = []
        if self.section:
            loc.append(f"Section: {self.section}")
        if self.page is not None:
            loc.append(f"Page: {self.page}")
        loc_str = f", {', '.join(loc)}" if loc else ""
        return f"[Doc: {self.filename}{loc_str}]"


class Citation(BaseModel):
    claim: str
    source_doc: str
    section: Optional[str] = None
    page: Optional[int] = None
    quote: str
    chunk_id: Optional[str] = None

    def format_bracket(self) -> str:
        loc = []
        if self.section:
            loc.append(f"Section: {self.section}")
        if self.page is not None:
            loc.append(f"Page: {self.page}")
        loc_str = f", {', '.join(loc)}" if loc else ""
        return f"[Doc: {self.source_doc}{loc_str}]"


class EntityRecord(BaseModel):
    entity_id: str
    name: str
    type: str = "general"
    attributes: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)


class CaseResolutionDraft(BaseModel):
    case_id: str
    resolution_text: str
    citations: List[Citation] = Field(default_factory=list)
    confidence_score: float = 1.0
    requires_escalation: bool = False
    escalation_reason: Optional[str] = None


class CriticEvaluation(BaseModel):
    is_grounded: bool
    grounding_score: float
    hallucination_score: float
    supported_claims: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    suggested_query_rewrite: Optional[str] = None
    feedback: str = ""


class AuditLogEntry(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}")
    timestamp: float = Field(default_factory=time.time)
    event_type: str
    user_or_entity: str
    details: Dict[str, Any] = Field(default_factory=dict)


class HumanReviewAction(BaseModel):
    case_id: str
    action: str  # "approve", "edit", "escalate", "reject"
    reviewer: str
    comments: Optional[str] = None
    modified_text: Optional[str] = None
