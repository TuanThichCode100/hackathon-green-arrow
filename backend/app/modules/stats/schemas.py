from pydantic import BaseModel
from typing import List

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
    recv_rate: float
    not_responded: int
    headmen_total: int
    headmen_confirmed: int
    active_alerts: int
