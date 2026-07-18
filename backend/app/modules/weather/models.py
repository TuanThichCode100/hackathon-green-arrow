from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.core.database import Base

class WeatherData(Base):
    __tablename__ = "weather_data"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    commune_id: Mapped[int] = mapped_column(Integer, index=True)
    temperature: Mapped[float] = mapped_column(Float, nullable=True)
    temp_min: Mapped[float] = mapped_column(Float, nullable=True)
    temp_max: Mapped[float] = mapped_column(Float, nullable=True)
    rainfall_1h: Mapped[float] = mapped_column(Float, nullable=True)
    rainfall_24h: Mapped[float] = mapped_column(Float, nullable=True)
    wind_speed: Mapped[float] = mapped_column(Float, nullable=True)
    wind_direction: Mapped[float] = mapped_column(Float, nullable=True)
    humidity: Mapped[float] = mapped_column(Float, nullable=True)
    visibility: Mapped[float] = mapped_column(Float, nullable=True)
    uv_index: Mapped[float] = mapped_column(Float, nullable=True)
    dew_point: Mapped[float] = mapped_column(Float, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
