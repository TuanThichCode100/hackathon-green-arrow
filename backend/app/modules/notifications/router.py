from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db
from app.common.schemas import APIResponse, PaginatedResponse
from app.modules.notifications import service, schemas

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("", response_model=APIResponse[PaginatedResponse[schemas.NotificationResponse]])
def get_all(page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    total, items = service.list_notifications(db, (page-1)*limit, limit)
    return {"data": {"total": total, "page": page, "limit": limit, "items": items}}
