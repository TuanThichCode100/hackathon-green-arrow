from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.schemas import APIResponse, PaginatedResponse
from app.core.auth import get_current_user_metadata, require_role
from app.core.dependencies import get_db
from app.modules.notifications import schemas, service


router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=APIResponse[PaginatedResponse[schemas.DispatchResponse]])
def get_all(page: int = 1, limit: int = 50, db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    commune_id = user["commune_id"] if user["role"] == "xa" else None
    total, items = service.list_dispatches(db, (page - 1) * limit, limit, commune_id)
    return {"data": {"total": total, "page": page, "limit": limit, "items": items}}


@router.get("/dispatches/{decision_id}/{commune_id}", response_model=APIResponse[schemas.DispatchDetailResponse])
def get_dispatch(decision_id: int, commune_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    if user["role"] == "xa" and user["commune_id"] != commune_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem đợt phân phối ngoài địa bàn phụ trách")
    return {"data": service.get_dispatch_detail(db, decision_id, commune_id)}


@router.post("/dispatches/{decision_id}/{commune_id}/activate", response_model=APIResponse[schemas.DispatchDetailResponse])
def activate_dispatch(decision_id: int, commune_id: int, body: schemas.DispatchActivationRequest, db: Session = Depends(get_db), user: dict = Depends(require_role(["xa"]))):
    if user["commune_id"] != commune_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Bạn không có quyền kích hoạt đợt phân phối ngoài địa bàn phụ trách")
    data = service.activate_dispatch(db, decision_id, commune_id, body.channels)
    db.commit()
    return {"data": data}


@router.post("/{notification_id}/sent", response_model=APIResponse[schemas.NotificationResponse])
def mark_sent(notification_id: int, db: Session = Depends(get_db), user: dict = Depends(require_role(["xa"]))):
    notification = service.mark_notification_sent(db, notification_id, user["commune_id"])
    db.commit(); db.refresh(notification)
    return {"data": notification}


@router.post("/{notification_id}/receipt", response_model=APIResponse[bool])
def record_receipt(notification_id: int, body: schemas.RecipientReceiptRequest, db: Session = Depends(get_db), user: dict = Depends(require_role(["xa"]))):
    service.record_recipient_receipt(db, notification_id, body.resident_id, user["commune_id"])
    db.commit()
    return {"data": True}
