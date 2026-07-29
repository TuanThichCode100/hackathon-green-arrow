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

class ResidentImport(BaseModel):
    records: list[ResidentCreate]

class ResidentImportResult(BaseModel):
    imported: int
