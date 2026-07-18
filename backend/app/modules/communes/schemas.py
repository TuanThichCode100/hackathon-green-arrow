from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class HamletResponse(BaseModel):
    id: int
    commune_id: int
    name: str
    headman_name: Optional[str]
    headman_phone: Optional[str]
    population: int
    model_config = ConfigDict(from_attributes=True)

class CommuneResponse(BaseModel):
    id: int
    name: str
    lat: float
    lng: float
    population: int
    notification_status: str
    disaster_type: Optional[str] = None
    disaster_icon: Optional[str] = None
    alert_status: Optional[str] = None
    recv_rate: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class CommuneDetailResponse(CommuneResponse):
    hamlets: List[HamletResponse] = []
