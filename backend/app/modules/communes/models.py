from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Commune(Base):
    __tablename__ = "communes"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    population: Mapped[int] = mapped_column(Integer, default=0)
    notification_status: Mapped[str] = mapped_column(String, default="not_sent")
    
    hamlets = relationship("Hamlet", back_populates="commune")

class Hamlet(Base):
    __tablename__ = "hamlets"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    commune_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String)
    headman_name: Mapped[str] = mapped_column(String, nullable=True)
    headman_phone: Mapped[str] = mapped_column(String, nullable=True)
    population: Mapped[int] = mapped_column(Integer, default=0)
    
    commune = relationship("Commune", back_populates="hamlets")
