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
