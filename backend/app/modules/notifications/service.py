from sqlalchemy.orm import Session
from app.modules.notifications.models import Notification

def list_notifications(db: Session, skip: int=0, limit: int=50):
    total = db.query(Notification).count()
    items = db.query(Notification).order_by(Notification.sent_at.desc()).offset(skip).limit(limit).all()
    return total, items
