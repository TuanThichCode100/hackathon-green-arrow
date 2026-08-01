from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.communes.models import Commune
from app.modules.notifications.models import Notification, NotificationRecipient
from app.modules.residents.models import Resident

def list_notifications(db: Session, skip: int=0, limit: int=50):
    total = db.query(Notification).count()
    rows = (
        db.query(Notification, Commune.name)
        .join(Commune, Commune.id == Notification.commune_id)
        .order_by(Notification.sent_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    notification_ids = [notification.id for notification, _ in rows]
    recipients_by_notification: dict[int, dict[str, int]] = {}
    if notification_ids:
        recipient_rows = (
            db.query(
                NotificationRecipient.notification_id,
                NotificationRecipient.status,
                func.count(NotificationRecipient.id),
            )
            .filter(NotificationRecipient.notification_id.in_(notification_ids))
            .group_by(NotificationRecipient.notification_id, NotificationRecipient.status)
            .all()
        )
        for notification_id, status, count in recipient_rows:
            recipients_by_notification.setdefault(notification_id, {})[status] = int(count)

    items = []
    for notification, commune_name in rows:
        counts = recipients_by_notification.get(notification.id, {})
        tracked_count = sum(counts.values())
        items.append({
            "id": notification.id,
            "commune_id": notification.commune_id,
            "commune_name": commune_name,
            "channel": notification.channel,
            "ethnic_language": notification.ethnic_language,
            "recipient_count": notification.recipient_count,
            "status": notification.status,
            "sent_at": notification.sent_at,
            "tracking_available": tracked_count > 0,
            "pending_count": counts.get("pending", 0),
            "sent_count": counts.get("sent", 0),
            "received_count": counts.get("received", 0) + counts.get("delivered", 0),
            "failed_count": counts.get("failed", 0),
        })
    return total, items


def create_notification_with_recipients(
    db: Session,
    *,
    commune_id: int,
    decision_id: int | None,
    channel: str,
    ethnic_language: str,
    content: str,
) -> Notification | None:
    """Create one dispatch batch and one pending record for every resident.

    A notification with no target residents is not persisted: there is nothing
    to deliver or track for that commune/channel combination.
    """
    residents = db.query(Resident.id).filter(Resident.commune_id == commune_id).all()
    if not residents:
        return None

    notification = Notification(
        commune_id=commune_id,
        decision_id=decision_id,
        channel=channel,
        ethnic_language=ethnic_language,
        content=content,
        recipient_count=len(residents),
        status="pending",
    )
    db.add(notification)
    db.flush()
    db.add_all([
        NotificationRecipient(
            notification_id=notification.id,
            resident_id=resident_id,
            status="pending",
        )
        for (resident_id,) in residents
    ])
    return notification


def mark_notification_sent(db: Session, notification_id: int) -> Notification:
    notification = db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Không tìm thấy đợt gửi cảnh báo")
    if notification.status == "failed":
        raise HTTPException(status_code=409, detail="Đợt gửi đã thất bại, cần tạo đợt gửi mới")

    notification.status = "sent"
    db.query(NotificationRecipient).filter(
        NotificationRecipient.notification_id == notification_id,
        NotificationRecipient.status == "pending",
    ).update({NotificationRecipient.status: "sent"}, synchronize_session=False)
    db.flush()
    return notification


def record_recipient_receipt(
    db: Session, notification_id: int, resident_id: int
) -> NotificationRecipient:
    recipient = (
        db.query(NotificationRecipient)
        .filter(
            NotificationRecipient.notification_id == notification_id,
            NotificationRecipient.resident_id == resident_id,
        )
        .first()
    )
    if not recipient:
        raise HTTPException(status_code=404, detail="Không tìm thấy người nhận trong đợt gửi này")

    recipient.status = "received"
    recipient.received_at = recipient.received_at or datetime.utcnow()
    db.flush()
    return recipient
