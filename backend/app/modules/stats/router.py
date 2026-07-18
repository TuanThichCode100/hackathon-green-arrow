from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.stats import service, schemas

router = APIRouter(prefix="/api/stats", tags=["Stats"])

@router.get("/overview", response_model=APIResponse[schemas.OverviewResponse])
def get_overview(time_range: str = "today", db: Session = Depends(get_db)):
    return {"data": service.calc_overview(db, time_range)}

@router.get("/channels", response_model=APIResponse[list])
def get_channels(time_range: str = "today", db: Session = Depends(get_db)):
    return {"data": service.calc_channel_stats(db, time_range) if hasattr(service, 'calc_channel_stats') else []}

@router.get("/ethnics", response_model=APIResponse[list])
def get_ethnics(db: Session = Depends(get_db)):
    return {"data": service.calc_ethnic_stats(db) if hasattr(service, 'calc_ethnic_stats') else []}

@router.get("/activities", response_model=APIResponse[list])
def get_activities(limit: int = 10, db: Session = Depends(get_db)):
    return {"data": service.get_recent_activities(db, limit) if hasattr(service, 'get_recent_activities') else []}
