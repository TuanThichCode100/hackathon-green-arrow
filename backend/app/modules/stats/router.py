from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.stats import service, schemas

router = APIRouter(prefix="/api/stats", tags=["Stats"])

@router.get("/overview", response_model=APIResponse[schemas.OverviewResponse])
def get_overview(time_range: str = "today", db: Session = Depends(get_db)):
    return {"data": service.calc_overview(db, time_range)}
