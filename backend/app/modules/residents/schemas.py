from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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


class ResidentImportRecord(BaseModel):
    """One parsed CSV row; business validation is intentionally per-row."""

    commune_id: int
    name: str = ""
    phone: str = ""
    ethnic: str = ""
    literate: bool = True
    source_row: int = 0


class ResidentImport(BaseModel):
    records: list[ResidentImportRecord] = Field(max_length=500)


class ResidentImportError(BaseModel):
    row: int
    reason: str


class ResidentImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[ResidentImportError]
