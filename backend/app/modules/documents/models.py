from sqlalchemy import Column, Integer, String, Text, Date, DateTime
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
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
