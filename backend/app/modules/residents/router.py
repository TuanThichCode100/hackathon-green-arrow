from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.schemas import APIResponse, PaginatedResponse
from app.core.auth import require_role
from app.core.dependencies import get_db
from app.modules.residents import schemas, service


router = APIRouter(prefix="/api/residents", tags=["Residents"])


@router.get("", response_model=APIResponse[PaginatedResponse[schemas.ResidentResponse]])
def get_residents(
    commune_id: Optional[int] = None,
    ethnic: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["tinh", "xa"])),
):
    if user.get("role") == "xa":
        commune_id = user.get("commune_id")
    total, items = service.list_residents(db, commune_id, ethnic, (page - 1) * limit, limit)
    return {"data": {"total": total, "page": page, "limit": limit, "items": items}}


@router.post("", response_model=APIResponse[schemas.ResidentResponse])
def create(
    data: schemas.ResidentCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["tinh", "xa"])),
):
    if user.get("role") == "xa":
        data.commune_id = user.get("commune_id")
    return {"data": service.create_resident(db, data)}


@router.post("/import", response_model=APIResponse[schemas.ResidentImportResult])
def import_csv(
    data: schemas.ResidentImport,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["tinh", "xa"])),
):
    if not data.records:
        raise HTTPException(status_code=422, detail="CSV chưa có bản ghi hợp lệ")
    records = []
    for record in data.records:
        row = record.model_dump()
        if user.get("role") == "xa":
            row["commune_id"] = user.get("commune_id")
        records.append(row)
    return {"data": service.import_residents(db, records)}


@router.put("/{id}", response_model=APIResponse[schemas.ResidentResponse])
def update(
    id: int,
    data: schemas.ResidentUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["tinh", "xa"])),
):
    commune_id = user.get("commune_id") if user.get("role") == "xa" else None
    resident = service.update_resident(db, id, data, commune_id)
    if not resident:
        raise HTTPException(status_code=404, detail="Không tìm thấy dân cư trong địa bàn được phép quản lý")
    return {"data": resident}


@router.delete("/{id}", response_model=APIResponse[bool])
def delete(
    id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["tinh", "xa"])),
):
    commune_id = user.get("commune_id") if user.get("role") == "xa" else None
    deleted = service.delete_resident(db, id, commune_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Không tìm thấy dân cư trong địa bàn được phép quản lý")
    return {"data": True}
