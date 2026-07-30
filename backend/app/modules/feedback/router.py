from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.schemas import APIResponse
from app.core.auth import get_current_user_metadata, require_role
from app.core.dependencies import get_db
from app.modules.feedback.models import Feedback, FeedbackNotificationRead
from app.modules.feedback.schemas import FeedbackCreate, FeedbackNotificationReadRequest, FeedbackResponse, FeedbackUpdate

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


@router.post("", response_model=APIResponse[FeedbackResponse])
def create_feedback(body: FeedbackCreate, db: Session = Depends(get_db), user: dict = Depends(require_role(["xa"]))):
    item = Feedback(
        category=body.category.strip(), source_area=(body.source_area or "").strip() or None,
        description=body.description.strip(), document_id=body.document_id,
        reporter_id=str(user.get("sub")), reporter_name=user.get("name") or user.get("email"),
        reporter_role="xa", commune_id=user.get("commune_id"), status="pending",
    )
    db.add(item); db.commit(); db.refresh(item)
    return {"data": item}


@router.get("", response_model=APIResponse[list[FeedbackResponse]])
def list_feedback(db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    query = db.query(Feedback)
    if user.get("role") != "tinh":
        query = query.filter(Feedback.reporter_id == str(user.get("sub")))
    return {"data": query.order_by(Feedback.created_at.desc()).all()}


@router.patch("/{feedback_id}", response_model=APIResponse[FeedbackResponse])
def update_feedback(feedback_id: int, body: FeedbackUpdate, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh"]))):
    item = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy phản ánh")
    if body.status in {"resolved", "dismissed"} and not (body.resolution or "").strip():
        raise HTTPException(status_code=422, detail="Cần ghi kết quả xử lý trước khi hoàn tất phản ánh")
    item.status = body.status
    item.resolution = (body.resolution or "").strip() or None
    item.resolved_by = str(user.get("sub")); item.resolved_by_name = user.get("name") or user.get("email")
    item.resolved_at = datetime.utcnow() if body.status in {"resolved", "dismissed"} else None
    db.commit(); db.refresh(item)
    return {"data": item}


@router.get("/notifications", response_model=APIResponse[list[dict]])
def feedback_notifications(db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    if user.get("role") != "tinh":
        return {"data": []}
    user_id = str(user.get("sub"))
    reads = {row.feedback_id for row in db.query(FeedbackNotificationRead).filter(FeedbackNotificationRead.user_id == user_id).all()}
    items = db.query(Feedback).filter(Feedback.status.in_(["pending", "reviewing"])).order_by(Feedback.created_at.desc()).limit(40).all()
    return {"data": [{
        "id": item.id, "source": "feedback", "actor_name": item.reporter_name, "actor_role": item.reporter_role,
        "title": "Phản ánh thông tin mới", "subtitle": f"{item.category}: {item.description[:160]}",
        "created_at": item.created_at, "read": item.id in reads, "actionable": False,
    } for item in items]}


@router.post("/notifications/read", response_model=APIResponse[bool])
def mark_feedback_notifications_read(body: FeedbackNotificationReadRequest, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh"]))):
    user_id = str(user.get("sub"))
    ids = list(set(body.feedback_ids))
    if not ids:
        return {"data": True}
    existing = {row.feedback_id for row in db.query(FeedbackNotificationRead).filter(FeedbackNotificationRead.user_id == user_id, FeedbackNotificationRead.feedback_id.in_(ids)).all()}
    for feedback_id in set(ids) - existing:
        db.add(FeedbackNotificationRead(feedback_id=feedback_id, user_id=user_id))
    db.commit()
    return {"data": True}
