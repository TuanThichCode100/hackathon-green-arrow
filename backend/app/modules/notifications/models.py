from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    commune_id: Mapped[int] = mapped_column(Integer, index=True)
    decision_id: Mapped[int] = mapped_column(Integer, nullable=True)
    channel: Mapped[str] = mapped_column(String)
    ethnic_language: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    recipient_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="pending")
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class NotificationRecipient(Base):
    __tablename__ = "notification_recipients"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    notification_id: Mapped[int] = mapped_column(Integer, ForeignKey("notifications.id"))
    resident_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="pending")
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
