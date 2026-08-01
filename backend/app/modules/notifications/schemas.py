from pydantic import BaseModel, ConfigDict
from datetime import datetime

class NotificationResponse(BaseModel):
    id: int
    commune_id: int
    channel: str
    ethnic_language: str
    recipient_count: int
    status: str
    sent_at: datetime
    commune_name: str | None = None
    tracking_available: bool = False
    pending_count: int = 0
    sent_count: int = 0
    received_count: int = 0
    failed_count: int = 0
    model_config = ConfigDict(from_attributes=True)


class RecipientReceiptRequest(BaseModel):
    resident_id: int
