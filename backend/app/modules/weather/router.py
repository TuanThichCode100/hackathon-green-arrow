from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.weather import service, schemas

router = APIRouter(prefix="/api/weather", tags=["Weather"])

@router.get("/current", response_model=APIResponse[schemas.WeatherResponse])
def get_current(db: Session = Depends(get_db)):
    data = service.get_current_weather(db)
    return {"data": data}

@router.get("/commune/{commune_id}", response_model=APIResponse[schemas.WeatherResponse])
def get_commune(commune_id: int, db: Session = Depends(get_db)):
    data = service.get_commune_weather(db, commune_id)
    return {"data": data}
