import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.external.open_meteo import OpenMeteoClient
from app.core.database import SessionLocal
from app.modules.predictions.models import Prediction

logger = logging.getLogger(__name__)

async def fetch_weather_task():
    logger.info("Fetching weather from Open-Meteo...")
    client = OpenMeteoClient()
    # Tọa độ trung tâm tỉnh Điện Biên
    lat, lng = 21.38, 103.01
    try:
        data = await client.fetch_weather(lat, lng)
        rain = data.get("current", {}).get("rain", 0)
        logger.info(f"Current rain in Dien Bien: {rain} mm")
        
        # Nếu lượng mưa > 10mm thì lưu dự báo nguy cơ (ví dụ mô phỏng)
        if rain > 10.0:
            db = SessionLocal()
            try:
                pred = Prediction(
                    commune_id=1,  # Giả sử gán tạm cho 1 xã trung tâm
                    disaster_type="Mưa lớn",
                    probability=0.85,
                    details=f"Lượng mưa vượt ngưỡng: {rain}mm",
                    severity="alert"
                )
                db.add(pred)
                db.commit()
                logger.info("Saved high rain prediction.")
            finally:
                db.close()
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Chạy mỗi 1 giờ
    scheduler.add_job(fetch_weather_task, 'interval', hours=1)
    scheduler.start()
    logger.info("Scheduler started. Open-Meteo will be called every 1 hour.")
    return scheduler
