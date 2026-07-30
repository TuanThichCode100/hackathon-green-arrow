from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    category: str = Field(min_length=2, max_length=80)
    source_area: str | None = Field(default=None, max_length=80)
    description: str = Field(min_length=10, max_length=4000)
    document_id: int | None = Field(default=None, gt=0)


class FeedbackUpdate(BaseModel):
    status: Literal["reviewing", "resolved", "dismissed"]
    resolution: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    id: int
    category: str
    source_area: str | None = None
    description: str
    document_id: int | None = None
    reporter_name: str
    reporter_role: str
    commune_id: int | None = None
    status: str
    resolution: str | None = None
    resolved_by_name: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class FeedbackNotificationReadRequest(BaseModel):
    feedback_ids: list[int] = Field(default_factory=list)
