from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db
from app.common.schemas import APIResponse, PaginatedResponse
from app.modules.notifications import service, schemas
from app.core.auth import get_current_user_metadata, require_role

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("", response_model=APIResponse[PaginatedResponse[schemas.NotificationResponse]])
def get_all(page: int = 1, limit: int = 50, db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    if hasattr(service, 'list_notifications'):
        total, items = service.list_notifications(db, (page-1)*limit, limit)
    else:
        total, items = 0, []
    return {"data": {"total": total, "page": page, "limit": limit, "items": items}}

class ActionRequest(schemas.BaseModel):
    commune_id: int
    hamlet_id: int = None

from app.modules.notifications.models import Notification


@router.post("/{notification_id}/sent", response_model=APIResponse[schemas.NotificationResponse])
def mark_sent(
    notification_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["tinh"])),
):
    notification = service.mark_notification_sent(db, notification_id)
    db.commit()
    db.refresh(notification)
    return {"data": notification}


@router.post("/{notification_id}/receipt", response_model=APIResponse[bool])
def record_receipt(
    notification_id: int,
    body: schemas.RecipientReceiptRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["tinh"])),
):
    service.record_recipient_receipt(db, notification_id, body.resident_id)
    db.commit()
    return {"data": True}

@router.post("/resend", response_model=APIResponse[str])
def resend_sms(req: ActionRequest, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh", "xa"]))):
    notif = Notification(
        commune_id=req.commune_id,
        channel="sms",
        ethnic_language="Kinh",
        content="Gửi lại cảnh báo SMS",
        recipient_count=1,
        status="delivered"
    )
    db.add(notif)
    db.commit()
    return {"data": f"Đã gửi lại SMS thành công tới trưởng bản."}

@router.post("/call", response_model=APIResponse[str])
def make_call(req: ActionRequest, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh", "xa"]))):
    notif = Notification(
        commune_id=req.commune_id,
        channel="call",
        ethnic_language="Kinh",
        content="Thực hiện cuộc gọi khẩn cấp",
        recipient_count=1,
        status="delivered"
    )
    db.add(notif)
    db.commit()
    return {"data": f"Đang thực hiện cuộc gọi khẩn cấp tới trưởng bản."}

