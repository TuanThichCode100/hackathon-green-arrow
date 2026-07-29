from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.agent import service, schemas
from app.core.auth import require_role, get_current_user_metadata

router = APIRouter(prefix="/api/agent", tags=["Agent"])

@router.get("/decisions", response_model=APIResponse[List[schemas.DecisionResponse]])
def list_decisions(page: int = 1, limit: int = 50, db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    return {"data": service.get_decisions(db, page, limit)}

@router.post("/draft", response_model=APIResponse[schemas.DecisionResponse])
def create_draft(req: schemas.DraftBulletinRequest, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh"]))):
    return {"data": service.draft_bulletin(db, req)}

@router.post("/approve/{decision_id}", response_model=APIResponse[schemas.DecisionResponse])
def approve_draft(decision_id: int, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh"]))):
    return {"data": service.approve_bulletin(db, decision_id)}

@router.post("/manual-trigger", response_model=APIResponse[schemas.DecisionResponse])
def trigger(req: schemas.ManualTriggerRequest, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh"]))):
    return {"data": service.manual_trigger(db, req)}
