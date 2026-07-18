import os
import json

def create_file(path, content):
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

files = {
    "app/modules/weather/__init__.py": "",
    "app/modules/weather/models.py": """
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
""",
    "app/modules/weather/schemas.py": """
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class WeatherResponse(BaseModel):
    id: int
    commune_id: int
    temperature: Optional[float]
    temp_min: Optional[float]
    temp_max: Optional[float]
    rainfall_1h: Optional[float]
    rainfall_24h: Optional[float]
    wind_speed: Optional[float]
    wind_direction: Optional[float]
    humidity: Optional[float]
    visibility: Optional[float]
    uv_index: Optional[float]
    dew_point: Optional[float]
    fetched_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ForecastItem(BaseModel):
    date: str
    temp_min: float
    temp_max: float
    rainfall: float
    wind_speed: float
    hazard_risk: str

class ForecastResponse(BaseModel):
    commune_id: int
    forecasts: List[ForecastItem]
""",
    "app/modules/weather/service.py": """
from sqlalchemy.orm import Session
from app.modules.weather.models import WeatherData

def get_current_weather(db: Session):
    return db.query(WeatherData).order_by(WeatherData.fetched_at.desc()).first()

def get_commune_weather(db: Session, commune_id: int):
    return db.query(WeatherData).filter(WeatherData.commune_id == commune_id).order_by(WeatherData.fetched_at.desc()).first()

def save_weather_data(db: Session, data: dict):
    wd = WeatherData(**data)
    db.add(wd)
    db.commit()
    db.refresh(wd)
    return wd
""",
    "app/modules/weather/router.py": """
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.weather import service, schemas

router = APIRouter(prefix="/api/weather", tags=["Weather"])

@router.get("/current", response_model=APIResponse[schemas.WeatherResponse])
def get_current(db: Session = Depends(get_db)):
    data = service.get_current_weather(db)
    return {"data": data}

@router.get("/commune/{commune_id}", response_model=APIResponse[schemas.WeatherResponse])
def get_commune(commune_id: int, db: Session = Depends(get_db)):
    data = service.get_commune_weather(db, commune_id)
    return {"data": data}
""",
    "app/modules/weather/tasks.py": """
import logging

logger = logging.getLogger(__name__)

async def cron_fetch_openmeteo():
    logger.info("Fetching weather from Open-Meteo...")
    # placeholder
""",
    "app/modules/communes/__init__.py": "",
    "app/modules/communes/models.py": """
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
""",
    "app/modules/communes/schemas.py": """
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class HamletResponse(BaseModel):
    id: int
    commune_id: int
    name: str
    headman_name: Optional[str]
    headman_phone: Optional[str]
    population: int
    model_config = ConfigDict(from_attributes=True)

class CommuneResponse(BaseModel):
    id: int
    name: str
    lat: float
    lng: float
    population: int
    notification_status: str
    disaster_type: Optional[str] = None
    disaster_icon: Optional[str] = None
    alert_status: Optional[str] = None
    recv_rate: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class CommuneDetailResponse(CommuneResponse):
    hamlets: List[HamletResponse] = []
""",
    "app/modules/communes/service.py": """
import json
from sqlalchemy.orm import Session
from app.modules.communes.models import Commune, Hamlet

def list_communes(db: Session, status_filter: str = None):
    q = db.query(Commune)
    if status_filter:
        q = q.filter(Commune.notification_status == status_filter)
    return q.all()

def get_commune(db: Session, commune_id: int):
    return db.query(Commune).filter(Commune.id == commune_id).first()

def get_hamlets(db: Session, commune_id: int):
    return db.query(Hamlet).filter(Hamlet.commune_id == commune_id).all()

def seed_communes(db: Session):
    if db.query(Commune).count() > 0:
        return
    try:
        with open("data/communes_seed.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            for i, c in enumerate(data):
                comm = Commune(
                    id=i+1,
                    name=c["name"],
                    lat=c.get("lat", 0.0),
                    lng=c.get("lng", 0.0),
                    population=c.get("population", 0)
                )
                db.add(comm)
                db.commit()
                db.refresh(comm)
                for h in c.get("hamlets", []):
                    hamlet = Hamlet(
                        commune_id=comm.id,
                        name=h["name"],
                        headman_name=h.get("headman"),
                        headman_phone=h.get("phone", "0987654321"),
                        population=h.get("population", 0)
                    )
                    db.add(hamlet)
            db.commit()
    except Exception as e:
        print("Seed error:", e)
""",
    "app/modules/communes/router.py": """
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.communes import service, schemas

router = APIRouter(prefix="/api/communes", tags=["Communes"])

@router.get("", response_model=APIResponse[List[schemas.CommuneResponse]])
def get_all(status: Optional[str] = None, db: Session = Depends(get_db)):
    data = service.list_communes(db, status)
    return {"data": data}

@router.get("/{commune_id}", response_model=APIResponse[schemas.CommuneDetailResponse])
def get_one(commune_id: int, db: Session = Depends(get_db)):
    comm = service.get_commune(db, commune_id)
    if not comm:
        raise HTTPException(status_code=404, detail="Commune not found")
    comm.hamlets = service.get_hamlets(db, commune_id)
    return {"data": comm}

@router.post("/seed", response_model=APIResponse[str])
def seed_db(db: Session = Depends(get_db)):
    service.seed_communes(db)
    return {"message": "Seeded successfully"}
""",
    "app/modules/residents/__init__.py": "",
    "app/modules/residents/models.py": """
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base

class Resident(Base):
    __tablename__ = "residents"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    commune_id: Mapped[int] = mapped_column(Integer, index=True)
    hamlet_id: Mapped[int] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String, unique=True, index=True)
    ethnic: Mapped[str] = mapped_column(String)
    literate: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
""",
    "app/modules/residents/schemas.py": """
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class ResidentCreate(BaseModel):
    commune_id: int
    hamlet_id: Optional[int] = None
    name: str
    phone: str
    ethnic: str
    literate: bool = True

class ResidentUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    ethnic: Optional[str] = None
    literate: Optional[bool] = None

class ResidentResponse(ResidentCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
""",
    "app/modules/residents/service.py": """
from sqlalchemy.orm import Session
from app.modules.residents.models import Resident

def list_residents(db: Session, commune_id: int = None, ethnic: str = None, skip: int = 0, limit: int = 50):
    q = db.query(Resident)
    if commune_id:
        q = q.filter(Resident.commune_id == commune_id)
    if ethnic:
        q = q.filter(Resident.ethnic == ethnic)
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return total, items

def create_resident(db: Session, data):
    r = Resident(**data.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r
""",
    "app/modules/residents/router.py": """
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.dependencies import get_db
from app.common.schemas import APIResponse, PaginatedResponse
from app.modules.residents import service, schemas

router = APIRouter(prefix="/api/residents", tags=["Residents"])

@router.get("", response_model=APIResponse[PaginatedResponse[schemas.ResidentResponse]])
def get_residents(commune_id: Optional[int] = None, ethnic: Optional[str] = None, page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    total, items = service.list_residents(db, commune_id, ethnic, (page-1)*limit, limit)
    return {"data": {"total": total, "page": page, "limit": limit, "items": items}}

@router.post("", response_model=APIResponse[schemas.ResidentResponse])
def create(data: schemas.ResidentCreate, db: Session = Depends(get_db)):
    return {"data": service.create_resident(db, data)}
""",
    "app/modules/predictions/__init__.py": "",
    "app/modules/predictions/models.py": """
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
""",
    "app/modules/predictions/schemas.py": """
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class PredictionResponse(BaseModel):
    id: int
    commune_id: int
    disaster_type: str
    probability: float
    severity: str
    predicted_at: datetime
    model_config = ConfigDict(from_attributes=True)
""",
    "app/modules/predictions/service.py": """
from sqlalchemy.orm import Session
from app.modules.predictions.models import Prediction

def get_latest_predictions(db: Session):
    # simplistic query for hackathon
    return db.query(Prediction).order_by(Prediction.predicted_at.desc()).limit(50).all()
""",
    "app/modules/predictions/router.py": """
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.predictions import service, schemas

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

@router.get("/latest", response_model=APIResponse[List[schemas.PredictionResponse]])
def get_latest(db: Session = Depends(get_db)):
    return {"data": service.get_latest_predictions(db)}
""",
    "app/modules/stats/__init__.py": "",
    "app/modules/stats/schemas.py": """
from pydantic import BaseModel
from typing import List

class ChannelStats(BaseModel):
    name: str
    sent: int
    delivered: int
    failed: int
    rate: float

class ChannelStatsResponse(BaseModel):
    channels: List[ChannelStats]

class OverviewResponse(BaseModel):
    total_pop: int
    recv_rate: float
    not_responded: int
    headmen_confirmed: int
    active_alerts: int
""",
    "app/modules/stats/service.py": """
from sqlalchemy.orm import Session

def calc_overview(db: Session, time_range: str):
    return {
        "total_pop": 642000,
        "recv_rate": 0.85,
        "not_responded": 96300,
        "headmen_confirmed": 210,
        "active_alerts": 3
    }
""",
    "app/modules/stats/router.py": """
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.stats import service, schemas

router = APIRouter(prefix="/api/stats", tags=["Stats"])

@router.get("/overview", response_model=APIResponse[schemas.OverviewResponse])
def get_overview(time_range: str = "today", db: Session = Depends(get_db)):
    return {"data": service.calc_overview(db, time_range)}
""",
    "app/modules/auth/__init__.py": "",
    "app/modules/auth/schemas.py": """
from pydantic import BaseModel

class LoginRequest(BaseModel):
    phone: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    role: str
    commune_id: int = None

class LoginResponse(BaseModel):
    token: str
    user: UserResponse
""",
    "app/modules/auth/service.py": """
def verify_user(phone: str, password: str):
    if password == "demo":
        return {"id": 1, "name": "Nguyễn Tiến Dũng", "role": "tinh"}
    return None
""",
    "app/modules/auth/router.py": """
from fastapi import APIRouter, HTTPException, Depends
from app.common.schemas import APIResponse
from app.modules.auth import service, schemas
from app.core.auth import get_current_user_role

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login", response_model=APIResponse[schemas.LoginResponse])
def login(req: schemas.LoginRequest):
    user = service.verify_user(req.phone, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"data": {"token": "mock-jwt-token", "user": user}}

@router.get("/me", response_model=APIResponse[dict])
def get_me(role: str = Depends(get_current_user_role)):
    return {"data": {"role": role}}
"""
}

# SEED DATA
communes_seed = [
    {"name": "Thanh Nưa", "lat": 21.300, "lng": 102.980, "population": 13500, "hamlets": [{"name": "Pom Lót", "headman": "Lò Văn Pâng", "population": 3200}]},
    {"name": "Mường Nhé", "lat": 21.170, "lng": 102.470, "population": 12400, "hamlets": [{"name": "Nậm Pố", "headman": "Vàng A Của", "population": 2100}]},
    {"name": "Tủa Chùa", "lat": 21.930, "lng": 103.380, "population": 11200, "hamlets": [{"name": "Tả Sìn Thàng", "headman": "Mùa A Kỷ", "population": 3100}]}
]

disaster_types = [
  {"id": "heavy_rain", "name": "Mưa lớn", "icon": "🌧️", "color": "#2563EB"},
  {"id": "landslide", "name": "Sạt lở", "icon": "⛰️", "color": "#B45309"},
  {"id": "storm", "name": "Dông lốc", "icon": "🌪️", "color": "#7C3AED"},
  {"id": "hail", "name": "Mưa đá", "icon": "🧊", "color": "#0891B2"},
  {"id": "flood", "name": "Lũ lụt", "icon": "🌊", "color": "#DC2626"}
]

files["data/communes_seed.json"] = json.dumps(communes_seed, ensure_ascii=False, indent=2)
files["data/disaster_types.json"] = json.dumps(disaster_types, ensure_ascii=False, indent=2)

for path, content in files.items():
    create_file(path, content)

print("Scaffolded phase 2 successfully.")
