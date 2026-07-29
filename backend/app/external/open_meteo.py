import httpx
from app.core.config import settings

class OpenMeteoClient:
    async def fetch_weather(self, lat: float, lng: float):
        url = f"{settings.OPEN_METEO_BASE_URL}/forecast?latitude={lat}&longitude={lng}&current=temperature_2m,rain,wind_speed_10m"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
