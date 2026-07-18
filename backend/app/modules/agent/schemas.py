from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class DecisionResponse(BaseModel):
    id: int
    trigger_type: str
    reasoning: str
    actions_json: str
    communes_affected: str
    bulletin_text: Optional[str] = None
    audio_tags: Optional[str] = None
    severity: Optional[str] = None
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ManualTriggerRequest(BaseModel):
    commune_ids: List[int]
    disaster_type: Optional[str] = None
    message: Optional[str] = None

class DraftBulletinRequest(BaseModel):
    commune_ids: List[int]
    disaster_type: str
