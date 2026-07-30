from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String, index=True)
    source_area: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text)
    document_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    reporter_id: Mapped[str] = mapped_column(String, index=True)
    reporter_name: Mapped[str] = mapped_column(String)
    reporter_role: Mapped[str] = mapped_column(String)
    commune_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FeedbackNotificationRead(Base):
    __tablename__ = "feedback_notification_reads"
    __table_args__ = (UniqueConstraint("feedback_id", "user_id", name="uq_feedback_notification_read"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    feedback_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    read_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
