from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base

class Resident(Base):
    __tablename__ = "residents"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    commune_id: Mapped[int] = mapped_column(Integer, ForeignKey("communes.id"), index=True)
    hamlet_id: Mapped[int] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String, unique=True, index=True)
    ethnic: Mapped[str] = mapped_column(String)
    # This records the language a resident primarily uses. Dispatching derives
    # its language groups from this fact; it is not merely a UI preference.
    primary_language: Mapped[str] = mapped_column(String, default="vi")
    literate: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
