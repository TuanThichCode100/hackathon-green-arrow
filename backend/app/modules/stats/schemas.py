from pydantic import BaseModel
from typing import List, Optional

class ChannelStats(BaseModel):
    name: str
    sent: int
    delivered: int
    failed: int
    rate: float

class ChannelStatsResponse(BaseModel):
    channels: List[ChannelStats]

class OverviewResponse(BaseModel):
    total_pop: int
    recv_rate: Optional[float]
    not_responded: Optional[int]
    headmen_total: int
    headmen_confirmed: Optional[int]
    active_alerts: int
