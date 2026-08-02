from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    commune_id: int
    channel: str
    ethnic_language: str
    recipient_count: int
    status: str
    sent_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DispatchResponse(BaseModel):
    decision_id: int
    commune_id: int
    commune_name: str
    total_residents: int
    notified_residents: int
    not_notified_residents: int
    channels: dict[str, list[str]]
    languages: list[str]
    created_at: datetime
    dispatched_at: datetime | None = None
    updated_at: datetime


class DispatchDetailResponse(DispatchResponse):
    people: list[dict[str, Any]]


class RecipientReceiptRequest(BaseModel):
    resident_id: int


class DispatchActivationRequest(BaseModel):
    channels: list[str]
