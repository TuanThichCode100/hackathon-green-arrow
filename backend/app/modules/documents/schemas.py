from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DocumentDraft(BaseModel):
    document_number: Optional[str] = None
    title: Optional[str] = None
    doc_type: Optional[str] = None
    issued_by: Optional[str] = None
    issued_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    llm_summary: Optional[str] = None
    required_actions: Optional[str] = None
    urgency: Optional[str] = None
    scope_type: str = "province"
    commune_ids: list[int] = Field(default_factory=list)
    show_original_to_province: bool = False


class DocumentResponse(DocumentDraft):
    id: int
    code: str
    status: str
    upload_status: str
    source_hash: Optional[str] = None
    original_filename: Optional[str] = None
    original_mime_type: Optional[str] = None
    commune_ids: list[int] = Field(default_factory=list)
    draft_expires_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DocumentPreviewResponse(BaseModel):
    document: DocumentResponse
    draft: DocumentDraft
    evidence: dict = Field(default_factory=dict)
    extraction_confidence: Optional[float] = None
    ai_analysis: dict = Field(default_factory=dict)


class OriginalViewRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class OriginalViewDecision(BaseModel):
    approve: bool
