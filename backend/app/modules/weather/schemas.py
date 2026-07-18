from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class WeatherResponse(BaseModel):
    id: int
    commune_id: int
    temperature: Optional[float]
    temp_min: Optional[float]
    temp_max: Optional[float]
    rainfall_1h: Optional[float]
    rainfall_24h: Optional[float]
    wind_speed: Optional[float]
    wind_direction: Optional[float]
    humidity: Optional[float]
    visibility: Optional[float]
    uv_index: Optional[float]
    dew_point: Optional[float]
    fetched_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ForecastItem(BaseModel):
    date: str
    temp_min: float
    temp_max: float
    rainfall: float
    wind_speed: float
    hazard_risk: str

class ForecastResponse(BaseModel):
    commune_id: int
    forecasts: List[ForecastItem]
