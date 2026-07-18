from sqlalchemy.orm import Session
from app.modules.weather.models import WeatherData

def get_current_weather(db: Session):
    return db.query(WeatherData).order_by(WeatherData.fetched_at.desc()).first()

def get_commune_weather(db: Session, commune_id: int):
    return db.query(WeatherData).filter(WeatherData.commune_id == commune_id).order_by(WeatherData.fetched_at.desc()).first()

def save_weather_data(db: Session, data: dict):
    wd = WeatherData(**data)
    db.add(wd)
    db.commit()
    db.refresh(wd)
    return wd
