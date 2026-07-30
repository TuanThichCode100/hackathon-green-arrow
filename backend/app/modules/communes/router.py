from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.communes import service, schemas
from app.core.auth import require_role

router = APIRouter(prefix="/api/communes", tags=["Communes"])

@router.get("", response_model=APIResponse[List[schemas.CommuneResponse]])
def get_all(status: Optional[str] = None, db: Session = Depends(get_db)):
    data = service.list_communes(db, status)
    return {"data": data}

@router.get("/{commune_id}", response_model=APIResponse[schemas.CommuneDetailResponse])
def get_one(commune_id: int, db: Session = Depends(get_db)):
    comm = service.get_commune(db, commune_id)
    if not comm:
        raise HTTPException(status_code=404, detail="Commune not found")
    comm.hamlets = service.get_hamlets(db, commune_id)
    return {"data": comm}

@router.post("/seed", response_model=APIResponse[str])
def seed_db(db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh"]))):
    service.seed_communes(db)
    return {"message": "Seeded successfully"}
