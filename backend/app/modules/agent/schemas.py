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
