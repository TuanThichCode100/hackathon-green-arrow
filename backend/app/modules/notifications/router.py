from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db
from app.common.schemas import APIResponse, PaginatedResponse
from app.modules.notifications import service, schemas

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("", response_model=APIResponse[PaginatedResponse[schemas.NotificationResponse]])
def get_all(page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    if hasattr(service, 'list_notifications'):
        total, items = service.list_notifications(db, (page-1)*limit, limit)
    else:
        total, items = 0, []
    return {"data": {"total": total, "page": page, "limit": limit, "items": items}}

class ActionRequest(schemas.BaseModel):
    commune_id: int
    hamlet_id: int = None

@router.post("/resend", response_model=APIResponse[str])
def resend_sms(req: ActionRequest, db: Session = Depends(get_db)):
    # Mocking successful SMS resend
    return {"data": f"Đã gửi lại SMS thành công tới trưởng bản."}

@router.post("/call", response_model=APIResponse[str])
def make_call(req: ActionRequest, db: Session = Depends(get_db)):
    # Mocking successful Auto-call
    return {"data": f"Đang thực hiện cuộc gọi khẩn cấp tới trưởng bản."}
