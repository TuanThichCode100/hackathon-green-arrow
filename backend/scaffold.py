import os

def create_file(path, content):
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

files = {
    "app/__init__.py": "",
    "app/core/__init__.py": "",
    "app/common/__init__.py": "",
    "app/modules/__init__.py": "",
    "app/external/__init__.py": "",
    "data/.gitkeep": "",
    "data/uploads/.gitkeep": "",
    ".env.example": """
DATABASE_URL=sqlite:///./data/greenforecast.db
LLM_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key
""",
    "requirements.txt": """
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
alembic>=1.13.0
httpx>=0.27.0
apscheduler>=3.10.0
python-multipart>=0.0.9
google-genai>=1.0.0
""",
    ".gitignore": """
__pycache__/
*.py[cod]
.env
*.db
data/uploads/*
.venv/
""",
    "app/core/config.py": """
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "GreenForecast API"
    DATABASE_URL: str = "sqlite:///./data/greenforecast.db"
    LLM_API_KEY: str = ""
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    SECRET_KEY: str = "supersecret"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
""",
    "app/core/database.py": """
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def init_db():
    Base.metadata.create_all(bind=engine)
""",
    "app/core/auth.py": """
from fastapi import Header, HTTPException, Depends

def require_role(allowed_roles: list[str]):
    def role_checker(x_user_role: str = Header("tinh")):
        if x_user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden: Insufficient role")
        return x_user_role
    return role_checker

def get_current_user_role(x_user_role: str = Header("tinh")):
    return x_user_role
""",
    "app/core/dependencies.py": """
from app.core.database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",
    "app/common/schemas.py": """
from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    status: str = "success"
    message: str = ""
    data: Optional[T] = None

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    limit: int
    items: List[T]
""",
    "app/common/utils.py": """
from datetime import datetime

def format_number(n: int) -> str:
    return f"{n:,}".replace(",", ".")

def format_date(dt: datetime) -> str:
    return dt.strftime("%H:%M %d/%m/%Y")
""",
    "app/main.py": """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db

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

@app.get("/")
def root():
    return {"message": "GreenForecast API is running"}
"""
}

for path, content in files.items():
    create_file(path, content)

print("Scaffolded backend successfully.")
