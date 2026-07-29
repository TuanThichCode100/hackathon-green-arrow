from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.dependencies import get_db
from app.common.schemas import APIResponse, PaginatedResponse
from app.modules.residents import service, schemas
from app.core.auth import require_role

router = APIRouter(prefix="/api/residents", tags=["Residents"])

@router.get("", response_model=APIResponse[PaginatedResponse[schemas.ResidentResponse]])
def get_residents(commune_id: Optional[int] = None, ethnic: Optional[str] = None, page: int = 1, limit: int = 50, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh", "xa"]))):
    if user.get("role") == "xa":
        commune_id = user.get("commune_id")
    total, items = service.list_residents(db, commune_id, ethnic, (page-1)*limit, limit)
    return {"data": {"total": total, "page": page, "limit": limit, "items": items}}

@router.post("", response_model=APIResponse[schemas.ResidentResponse])
def create(data: schemas.ResidentCreate, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh", "xa"]))):
    if user.get("role") == "xa":
        data.commune_id = user.get("commune_id")
    return {"data": service.create_resident(db, data)}

@router.post("/import", response_model=APIResponse[schemas.ResidentImportResult])
def import_csv(data: schemas.ResidentImport, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh", "xa"]))):
    if not data.records:
        raise HTTPException(status_code=422, detail="CSV chưa có bản ghi hợp lệ")
    records = []
    for r in data.records:
        r_dict = r.model_dump()
        if user.get("role") == "xa":
            r_dict["commune_id"] = user.get("commune_id")
        records.append(r_dict)
    return {"data": {"imported": service.import_csv(db, records)}}

@router.put("/{id}", response_model=APIResponse[schemas.ResidentResponse])
def update(id: int, data: schemas.ResidentUpdate, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh", "xa"]))):
    if user.get("role") == "xa":
        data.commune_id = user.get("commune_id")
    # Cần kiểm tra xem resident đó có thuộc xã của user không trong service (tạm thời để service lo)
    res = service.update_resident(db, id, data)
    if not res:
        raise HTTPException(status_code=404, detail="Resident not found")
    return {"data": res}

@router.delete("/{id}", response_model=APIResponse[bool])
def delete(id: int, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh", "xa"]))):
    res = service.delete_resident(db, id)
    if not res:
        raise HTTPException(status_code=404, detail="Resident not found")
    return {"data": True}
