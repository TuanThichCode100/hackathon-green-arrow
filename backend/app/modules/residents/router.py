from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.dependencies import get_db
from app.common.schemas import APIResponse, PaginatedResponse
from app.modules.residents import service, schemas

router = APIRouter(prefix="/api/residents", tags=["Residents"])

@router.get("", response_model=APIResponse[PaginatedResponse[schemas.ResidentResponse]])
def get_residents(commune_id: Optional[int] = None, ethnic: Optional[str] = None, page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    total, items = service.list_residents(db, commune_id, ethnic, (page-1)*limit, limit)
    return {"data": {"total": total, "page": page, "limit": limit, "items": items}}

@router.post("", response_model=APIResponse[schemas.ResidentResponse])
def create(data: schemas.ResidentCreate, db: Session = Depends(get_db)):
    return {"data": service.create_resident(db, data)}
