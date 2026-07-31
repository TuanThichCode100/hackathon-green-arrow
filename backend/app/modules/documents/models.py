import json

from sqlalchemy import Boolean, Column, Integer, String, Text, Date, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    doc_type: Mapped[str] = mapped_column(String)
    issued_by: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    llm_summary: Mapped[str] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")
    upload_status: Mapped[str] = mapped_column(String, default="approved", index=True)
    processing_stage: Mapped[str] = mapped_column(String, nullable=True)
    document_number: Mapped[str] = mapped_column(String, nullable=True)
    issued_date: Mapped[date] = mapped_column(Date, nullable=True)
    scope_type: Mapped[str] = mapped_column(String, default="province")
    commune_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    required_actions: Mapped[str] = mapped_column(Text, nullable=True)
    urgency: Mapped[str] = mapped_column(String, nullable=True)
    source_hash: Mapped[str] = mapped_column(String, nullable=True)
    original_filename: Mapped[str] = mapped_column(String, nullable=True)
    original_mime_type: Mapped[str] = mapped_column(String, nullable=True)
    draft_analysis_path: Mapped[str] = mapped_column(String, nullable=True)
    draft_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    uploaded_by: Mapped[str] = mapped_column(String, nullable=True, index=True)
    uploaded_by_name: Mapped[str] = mapped_column(String, nullable=True)
    show_original_to_province: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[str] = mapped_column(String, nullable=True)
    deleted_by_name: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @property
    def commune_ids(self) -> list[int]:
        try:
            values = json.loads(self.commune_ids_json or "[]")
            return [value for value in values if isinstance(value, int)]
        except (TypeError, ValueError):
            return []


class DocumentAuditEvent(Base):
    __tablename__ = "document_audit_events"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, index=True)
    actor_id: Mapped[str] = mapped_column(String)
    actor_name: Mapped[str] = mapped_column(String)
    actor_role: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String, index=True)
    detail: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DocumentNotificationRead(Base):
    __tablename__ = "document_notification_reads"
    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_document_notification_read"),)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    read_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DocumentViewRequest(Base):
    __tablename__ = "document_view_requests"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, index=True)
    requester_id: Mapped[str] = mapped_column(String, index=True)
    requester_name: Mapped[str] = mapped_column(String)
    requester_role: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    approved_by: Mapped[str] = mapped_column(String, nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    view_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
