from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.predictions import service, schemas

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

@router.get("/latest", response_model=APIResponse[List[schemas.PredictionResponse]])
def get_latest(db: Session = Depends(get_db)):
    return {"data": service.get_latest_predictions(db)}
