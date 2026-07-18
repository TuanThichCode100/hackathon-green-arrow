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

@router.put("/{id}", response_model=APIResponse[schemas.ResidentResponse])
def update(id: int, data: schemas.ResidentUpdate, db: Session = Depends(get_db)):
    res = service.update_resident(db, id, data)
    if not res:
        raise HTTPException(status_code=404, detail="Resident not found")
    return {"data": res}

@router.delete("/{id}", response_model=APIResponse[bool])
def delete(id: int, db: Session = Depends(get_db)):
    res = service.delete_resident(db, id)
    if not res:
        raise HTTPException(status_code=404, detail="Resident not found")
    return {"data": True}

@router.post("/import", response_model=APIResponse[int])
def import_csv(data: schemas.ResidentImport, db: Session = Depends(get_db)):
    # Data is sent from frontend after parsing CSV/Excel
    return {"data": service.import_csv(db, [r.model_dump() for r in data.records])}
