from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base

class AgentDecision(Base):
    __tablename__ = "agent_decisions"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    trigger_type: Mapped[str] = mapped_column(String)
    reasoning: Mapped[str] = mapped_column(Text)
    actions_json: Mapped[str] = mapped_column(Text)
    communes_affected: Mapped[str] = mapped_column(Text)
    bulletin_text: Mapped[str] = mapped_column(Text, nullable=True)
    audio_tags: Mapped[str] = mapped_column(String, nullable=True)
    severity: Mapped[str] = mapped_column(String, nullable=True)
    notifications_sent: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
