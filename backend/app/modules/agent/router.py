from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.agent import service, schemas

router = APIRouter(prefix="/api/agent", tags=["Agent"])

@router.get("/decisions", response_model=APIResponse[List[schemas.DecisionResponse]])
def list_decisions(page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    return {"data": service.get_decisions(db, page, limit)}

@router.post("/manual-trigger", response_model=APIResponse[schemas.DecisionResponse])
def trigger(req: schemas.ManualTriggerRequest, db: Session = Depends(get_db)):
    return {"data": service.manual_trigger(db, req)}
