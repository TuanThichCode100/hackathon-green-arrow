from pydantic import BaseModel, ConfigDict
from datetime import datetime

class PredictionResponse(BaseModel):
    id: int
    commune_id: int
    disaster_type: str
    probability: float
    severity: str
    predicted_at: datetime
    model_config = ConfigDict(from_attributes=True)
