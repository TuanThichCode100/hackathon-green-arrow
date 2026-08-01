from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.modules.communes.models import Commune, Hamlet
from app.modules.residents.models import Resident
from app.modules.notifications.models import Notification, NotificationRecipient
from app.modules.agent.models import AgentDecision

def get_start_date(time_range: str) -> datetime:
    now = datetime.utcnow()
    if time_range == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == "3days":
        return now - timedelta(days=3)
    elif time_range == "week":
        return now - timedelta(days=7)
    elif time_range == "month":
        return now - timedelta(days=30)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)

def calc_overview(db: Session, time_range: str):
    start_date = get_start_date(time_range)
    total_pop = db.query(func.count(Resident.id)).scalar() or 0

    # Only actual per-resident receipts are evidence of delivery. Aggregate
    # notification target counts must not be presented as confirmed receipts.
    receipt_query = db.query(NotificationRecipient).filter(
        NotificationRecipient.received_at >= start_date,
        NotificationRecipient.status.in_(["received", "delivered"]),
    )
    has_receipt_evidence = receipt_query.first() is not None
    confirmed_residents = (
        db.query(func.count(func.distinct(NotificationRecipient.resident_id)))
        .filter(
            NotificationRecipient.received_at >= start_date,
            NotificationRecipient.status.in_(["received", "delivered"]),
        )
        .scalar()
        or 0
    )
    recv_rate = (
        min(1.0, confirmed_residents / total_pop)
        if has_receipt_evidence and total_pop > 0
        else None
    )
    not_responded = int(total_pop * (1 - recv_rate)) if recv_rate is not None else None

    headmen_total = db.query(func.count(Hamlet.id)).scalar() or 0
    headmen_confirmed = int(headmen_total * recv_rate) if recv_rate is not None else None
    
    active_alerts = db.query(func.count(Commune.id)).filter(Commune.notification_status.in_(["sent", "delivered"])).scalar() or 0

    return {
        "total_pop": int(total_pop),
        "recv_rate": round(recv_rate, 2) if recv_rate is not None else None,
        "not_responded": not_responded,
        "headmen_total": headmen_total,
        "headmen_confirmed": headmen_confirmed,
        "active_alerts": active_alerts
    }

def calc_channel_stats(db: Session, time_range: str):
    start_date = get_start_date(time_range)
    channels = ["zalo", "sms", "call"]
    stats = []
    
    for ch in channels:
        sent = db.query(func.sum(Notification.recipient_count)).filter(
            Notification.channel == ch,
            Notification.status.in_(["sent", "delivered"]),
            Notification.sent_at >= start_date,
        ).scalar() or 0
        delivered = db.query(func.count(NotificationRecipient.id)).join(
            Notification,
            Notification.id == NotificationRecipient.notification_id,
        ).filter(
            Notification.channel == ch,
            NotificationRecipient.status.in_(["received", "delivered"]),
            NotificationRecipient.received_at >= start_date,
        ).scalar() or 0
        failed = db.query(func.sum(Notification.recipient_count)).filter(
            Notification.channel == ch, 
            Notification.status == 'failed',
            Notification.sent_at >= start_date
        ).scalar() or 0
        
        rate = delivered / sent if sent > 0 else 0
        
        stats.append({
            "name": ch,
            "sent": int(sent),
            "delivered": int(delivered),
            "failed": int(failed),
            "rate": round(rate, 2)
        })
    return stats

def calc_ethnic_stats(db: Session):
    # Group by ethnic
    results = db.query(Resident.ethnic, func.count(Resident.id)).group_by(Resident.ethnic).all()
    
    stats = []
    colors = {"Mông": "#3FD98A", "Thái": "#25ADE3", "Kinh": "#E8A93B", "Khơ Mú": "#E23D3D", "Dao": "#9B51E0"}
    
    total = sum(count for _, count in results)
    if total == 0: return []

    for ethnic, count in results:
        stats.append({
            "name": ethnic,
            "value": count,
            "pct": int((count / total) * 100),
            "color": colors.get(ethnic, "#95A5A6")
        })
    
    return sorted(stats, key=lambda x: x["value"], reverse=True)

def get_recent_activities(db: Session, limit: int = 10):
    notifs = db.query(Notification).order_by(Notification.sent_at.desc()).limit(limit).all()
    decisions = db.query(AgentDecision).order_by(AgentDecision.created_at.desc()).limit(limit).all()
    
    activities = []
    
    for n in notifs:
        activities.append({
            "time": n.sent_at.strftime("%H:%M:%S"),
            "msg": f"Đã gửi {n.recipient_count} tin qua {n.channel.upper()} ({n.ethnic_language})",
            "type": "success" if n.status == "delivered" else "warning",
            "timestamp": n.sent_at
        })
        
    for d in decisions:
        activities.append({
            "time": d.created_at.strftime("%H:%M:%S"),
            "msg": f"AI Agent ra quyết định: {d.reasoning[:50]}...",
            "type": "info",
            "timestamp": d.created_at
        })
        
    # Sort combined list by timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Strip timestamp before returning
    return [{"time": a["time"], "msg": a["msg"], "type": a["type"]} for a in activities[:limit]]
