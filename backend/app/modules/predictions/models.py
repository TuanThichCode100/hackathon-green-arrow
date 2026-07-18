from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base

class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    commune_id: Mapped[int] = mapped_column(Integer, index=True)
    disaster_type: Mapped[str] = mapped_column(String)
    probability: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String)
    predicted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
