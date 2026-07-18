import os

def create_file(path, content):
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

files = {
    "app/modules/agent/__init__.py": "",
    "app/modules/agent/models.py": """
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
    notifications_sent: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
""",
    "app/modules/agent/schemas.py": """
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class DecisionResponse(BaseModel):
    id: int
    trigger_type: str
    reasoning: str
    actions_json: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ManualTriggerRequest(BaseModel):
    commune_ids: List[int]
    disaster_type: Optional[str] = None
    message: Optional[str] = None
""",
    "app/modules/agent/service.py": """
from sqlalchemy.orm import Session
from app.modules.agent.models import AgentDecision

def get_decisions(db: Session, page: int = 1, limit: int = 50):
    return db.query(AgentDecision).order_by(AgentDecision.created_at.desc()).offset((page-1)*limit).limit(limit).all()

def manual_trigger(db: Session, request):
    dec = AgentDecision(
        trigger_type="manual_trigger",
        reasoning="Cán bộ kích hoạt thủ công",
        actions_json="[]",
        communes_affected=",".join(map(str, request.commune_ids)),
        status="executing"
    )
    db.add(dec)
    db.commit()
    db.refresh(dec)
    return dec
""",
    "app/modules/agent/router.py": """
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.agent import service, schemas

router = APIRouter(prefix="/api/agent", tags=["Agent"])

@router.get("/decisions", response_model=APIResponse[List[schemas.DecisionResponse]])
def list_decisions(page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    return {"data": service.get_decisions(db, page, limit)}

@router.post("/manual-trigger", response_model=APIResponse[schemas.DecisionResponse])
def trigger(req: schemas.ManualTriggerRequest, db: Session = Depends(get_db)):
    return {"data": service.manual_trigger(db, req)}
""",
    "app/modules/notifications/__init__.py": "",
    "app/modules/notifications/models.py": """
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
""",
    "app/modules/notifications/schemas.py": """
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class NotificationResponse(BaseModel):
    id: int
    commune_id: int
    channel: str
    recipient_count: int
    status: str
    sent_at: datetime
    model_config = ConfigDict(from_attributes=True)
""",
    "app/modules/notifications/service.py": """
from sqlalchemy.orm import Session
from app.modules.notifications.models import Notification

def list_notifications(db: Session, skip: int=0, limit: int=50):
    total = db.query(Notification).count()
    items = db.query(Notification).order_by(Notification.sent_at.desc()).offset(skip).limit(limit).all()
    return total, items
""",
    "app/modules/notifications/router.py": """
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db
from app.common.schemas import APIResponse, PaginatedResponse
from app.modules.notifications import service, schemas

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("", response_model=APIResponse[PaginatedResponse[schemas.NotificationResponse]])
def get_all(page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    total, items = service.list_notifications(db, (page-1)*limit, limit)
    return {"data": {"total": total, "page": page, "limit": limit, "items": items}}
""",
    "app/modules/documents/__init__.py": "",
    "app/modules/documents/models.py": """
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
""",
    "app/modules/documents/schemas.py": """
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional

class DocumentResponse(BaseModel):
    id: int
    code: str
    title: str
    doc_type: str
    issued_by: str
    llm_summary: Optional[str]
    start_date: date
    end_date: date
    status: str
    model_config = ConfigDict(from_attributes=True)
""",
    "app/modules/documents/service.py": """
from sqlalchemy.orm import Session
from app.modules.documents.models import Document

def list_documents(db: Session):
    return db.query(Document).order_by(Document.created_at.desc()).all()
""",
    "app/modules/documents/router.py": """
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.documents import service, schemas

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.get("", response_model=APIResponse[List[schemas.DocumentResponse]])
def get_docs(db: Session = Depends(get_db)):
    return {"data": service.list_documents(db)}
""",
    "app/modules/disaster_types/__init__.py": "",
    "app/modules/disaster_types/router.py": """
import json
from fastapi import APIRouter
from app.common.schemas import APIResponse

router = APIRouter(prefix="/api/disaster-types", tags=["Disaster Types"])

@router.get("", response_model=APIResponse[list])
def get_types():
    with open("data/disaster_types.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"data": data}
""",
    "app/external/open_meteo.py": """
import httpx
from app.core.config import settings

class OpenMeteoClient:
    async def fetch_weather(self, lat: float, lng: float):
        url = f"{settings.OPEN_METEO_BASE_URL}/forecast?latitude={lat}&longitude={lng}&current=temperature_2m,rain,wind_speed_10m"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            return resp.json()
""",
    "app/external/llm_client.py": """
class LLMClient:
    async def summarize_document(self, content: str) -> str:
        return "Mock summary"
""",
    "app/external/zalo_client.py": """
class ZaloClient:
    async def send_message(self, phone: str, content: str):
        return {"status": "success"}
""",
    "app/external/sms_client.py": """
class SMSClient:
    async def send_sms(self, phone: str, content: str):
        return {"status": "success"}
""",
    "app/external/tts_client.py": """
class TTSClient:
    async def generate_audio(self, text: str, lang="vi"):
        return "http://mock-audio-url"
"""
}

# UPDATE MAIN.PY to include routers
main_py = """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db

# Import routers safely
routers = []
try:
    from app.modules.weather.router import router as weather_router
    routers.append(weather_router)
    from app.modules.communes.router import router as communes_router
    routers.append(communes_router)
    from app.modules.residents.router import router as residents_router
    routers.append(residents_router)
    from app.modules.predictions.router import router as predictions_router
    routers.append(predictions_router)
    from app.modules.stats.router import router as stats_router
    routers.append(stats_router)
    from app.modules.auth.router import router as auth_router
    routers.append(auth_router)
    from app.modules.agent.router import router as agent_router
    routers.append(agent_router)
    from app.modules.notifications.router import router as notif_router
    routers.append(notif_router)
    from app.modules.documents.router import router as docs_router
    routers.append(docs_router)
    from app.modules.disaster_types.router import router as disaster_router
    routers.append(disaster_router)
except ImportError as e:
    print(f"Warning: A router could not be imported. {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in routers:
    app.include_router(r)

@app.get("/")
def root():
    return {"message": "GreenForecast API is running"}
"""

files["app/main.py"] = main_py

for path, content in files.items():
    create_file(path, content)

print("Scaffolded phase 3 successfully.")
