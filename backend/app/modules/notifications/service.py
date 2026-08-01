from collections import defaultdict
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.communes.models import Commune
from app.modules.notifications.models import Notification, NotificationRecipient
from app.modules.residents.models import Resident


LANGUAGE_LABELS = {"vi": "Tiếng Việt", "hmn": "Tiếng Mông", "tai": "Tiếng Thái", "khmu": "Tiếng Khơ Mú", "dao": "Tiếng Dao"}
ACTIVE_DELIVERY = {"sent", "received", "delivered"}


def _language_label(code: str) -> str:
    return LANGUAGE_LABELS.get(code, code or "Chưa xác định")


def _create_batch(db: Session, *, commune_id: int, decision_id: int | None, channel: str, language: str, content: str, resident_ids: list[int]) -> Notification:
    waiting_content = language != "vi" and not content
    now = datetime.utcnow()
    notification = Notification(
        commune_id=commune_id,
        decision_id=decision_id,
        channel=channel,
        ethnic_language=language,
        content=content,
        recipient_count=len(resident_ids),
        status="waiting_content" if waiting_content else "pending",
        created_at=now,
        updated_at=now,
    )
    db.add(notification)
    db.flush()
    recipient_status = "waiting_content" if waiting_content else "pending"
    db.add_all([NotificationRecipient(notification_id=notification.id, resident_id=resident_id, status=recipient_status) for resident_id in resident_ids])
    return notification


def create_notification_with_recipients(db: Session, *, commune_id: int, decision_id: int | None, channel: str, ethnic_language: str, content: str) -> Notification | None:
    resident_ids = [resident_id for (resident_id,) in db.query(Resident.id).filter(Resident.commune_id == commune_id).all()]
    if not resident_ids:
        return None
    return _create_batch(db, commune_id=commune_id, decision_id=decision_id, channel=channel, language=ethnic_language, content=content, resident_ids=resident_ids)


def create_language_dispatches(db: Session, *, commune_id: int, decision_id: int, channel: str, vietnamese_content: str) -> list[Notification]:
    groups: dict[str, list[int]] = defaultdict(list)
    for resident_id, language in db.query(Resident.id, Resident.preferred_alert_language).filter(Resident.commune_id == commune_id):
        groups[language or "vi"].append(resident_id)
    return [
        _create_batch(db, commune_id=commune_id, decision_id=decision_id, channel=channel, language=language, content=vietnamese_content if language == "vi" else "", resident_ids=resident_ids)
        for language, resident_ids in groups.items()
    ]


def mark_notification_sent(db: Session, notification_id: int) -> Notification:
    notification = db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Không tìm thấy đợt gửi cảnh báo")
    if notification.status in {"failed", "waiting_content"}:
        raise HTTPException(status_code=409, detail="Đợt gửi chưa có nội dung phù hợp hoặc đã thất bại")
    now = datetime.utcnow()
    notification.status, notification.dispatched_at, notification.updated_at = "sent", now, now
    db.query(NotificationRecipient).filter(NotificationRecipient.notification_id == notification_id, NotificationRecipient.status == "pending").update({NotificationRecipient.status: "sent"}, synchronize_session=False)
    db.flush()
    return notification


def record_recipient_receipt(db: Session, notification_id: int, resident_id: int) -> NotificationRecipient:
    recipient = db.query(NotificationRecipient).filter(NotificationRecipient.notification_id == notification_id, NotificationRecipient.resident_id == resident_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Không tìm thấy người nhận trong đợt gửi này")
    recipient.status = "received"
    recipient.received_at = recipient.received_at or datetime.utcnow()
    notification = db.get(Notification, notification_id)
    if notification:
        notification.updated_at = datetime.utcnow()
    db.flush()
    return recipient


def _dispatch_data(db: Session, decision_id: int, commune_id: int) -> dict:
    notifications = db.query(Notification).filter(Notification.decision_id == decision_id, Notification.commune_id == commune_id).order_by(Notification.created_at.asc()).all()
    if not notifications:
        raise HTTPException(status_code=404, detail="Không tìm thấy đợt phân phối")
    notification_ids = [item.id for item in notifications]
    commune = db.get(Commune, commune_id)
    recipients = db.query(NotificationRecipient, Resident, Notification).join(Resident, Resident.id == NotificationRecipient.resident_id).join(Notification, Notification.id == NotificationRecipient.notification_id).filter(NotificationRecipient.notification_id.in_(notification_ids)).all()
    by_resident: dict[int, dict] = {}
    for recipient, resident, notification in recipients:
        item = by_resident.setdefault(resident.id, {"id": resident.id, "name": resident.name, "phone": resident.phone, "ethnic": resident.ethnic, "preferred_alert_language": resident.preferred_alert_language, "channels": {}})
        item["channels"].setdefault(notification.channel, []).append({"language": notification.ethnic_language, "status": recipient.status})
    people = list(by_resident.values())
    for person in people:
        statuses = [delivery["status"] for channel in person["channels"].values() for delivery in channel]
        person["notified"] = any(status in ACTIVE_DELIVERY for status in statuses)
        person["progress"] = "Đã được thông báo" if person["notified"] else "Chưa được thông báo"
    people.sort(key=lambda item: (item["notified"], item["name"].casefold()))
    notified = sum(1 for item in people if item["notified"])
    by_channel: dict[str, list[str]] = defaultdict(list)
    for notification in notifications:
        by_channel[notification.channel].append(notification.status)
    return {"decision_id": decision_id, "commune_id": commune_id, "commune_name": commune.name if commune else f"Địa bàn #{commune_id}", "total_residents": len(people), "notified_residents": notified, "not_notified_residents": len(people) - notified, "people": people, "channels": {channel: sorted(set(statuses)) for channel, statuses in by_channel.items()}, "languages": sorted({_language_label(notification.ethnic_language) for notification in notifications}), "created_at": min(item.created_at for item in notifications), "dispatched_at": max((item.dispatched_at for item in notifications if item.dispatched_at), default=None), "updated_at": max(item.updated_at for item in notifications)}


def list_dispatches(db: Session, skip: int = 0, limit: int = 50):
    pairs = db.query(Notification.decision_id, Notification.commune_id).filter(Notification.decision_id.is_not(None)).group_by(Notification.decision_id, Notification.commune_id).order_by(func.max(Notification.created_at).desc()).all()
    data = [_dispatch_data(db, decision_id, commune_id) for decision_id, commune_id in pairs]
    return len(data), data[skip:skip + limit]


def get_dispatch_detail(db: Session, decision_id: int, commune_id: int):
    return _dispatch_data(db, decision_id, commune_id)
