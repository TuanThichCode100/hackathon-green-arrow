from sqlalchemy.orm import Session
from sqlalchemy import func
from app.modules.communes.models import Commune, Hamlet
from app.modules.residents.models import Resident
from app.modules.notifications.models import Notification
from app.modules.agent.models import AgentDecision

def calc_overview(db: Session, time_range: str):
    total_pop = db.query(func.sum(Commune.population)).scalar() or 0
    
    # Calculate receive rate based on notifications.
    # Total sent / Total population is a simplistic way for now.
    sent_notifications = db.query(func.sum(Notification.recipient_count)).filter(Notification.status == 'delivered').scalar() or 0
    recv_rate = min(1.0, sent_notifications / total_pop) if total_pop > 0 else 0

    not_responded = int(total_pop * (1 - recv_rate))
    
    headmen_total = db.query(func.count(Hamlet.id)).scalar() or 0
    # Simulate confirmation rate based on receive rate
    headmen_confirmed = int(headmen_total * recv_rate)
    
    active_alerts = db.query(func.count(Commune.id)).filter(Commune.notification_status.in_(["sent", "delivered"])).scalar() or 0

    return {
        "total_pop": int(total_pop),
        "recv_rate": round(recv_rate, 2),
        "not_responded": not_responded,
        "headmen_total": headmen_total,
        "headmen_confirmed": headmen_confirmed,
        "active_alerts": active_alerts
    }

def calc_channel_stats(db: Session, time_range: str):
    channels = ["zalo", "sms", "call"]
    stats = []
    
    for ch in channels:
        sent = db.query(func.sum(Notification.recipient_count)).filter(Notification.channel == ch).scalar() or 0
        delivered = db.query(func.sum(Notification.recipient_count)).filter(Notification.channel == ch, Notification.status == 'delivered').scalar() or 0
        failed = db.query(func.sum(Notification.recipient_count)).filter(Notification.channel == ch, Notification.status == 'failed').scalar() or 0
        
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
