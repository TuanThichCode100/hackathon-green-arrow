from sqlalchemy.orm import Session
from app.modules.agent.models import AgentDecision

def get_decisions(db: Session, page: int = 1, limit: int = 50):
    return db.query(AgentDecision).order_by(AgentDecision.created_at.desc()).offset((page-1)*limit).limit(limit).all()

def manual_trigger(db: Session, request):
    dec = AgentDecision(
        trigger_type="manual_trigger",
        reasoning="Cán bộ kích hoạt thủ công",
        actions_json="[]",
        communes_affected=",".join(map(str, request.commune_ids)),
        status="executing"
    )
    db.add(dec)
    db.commit()
    db.refresh(dec)
    return dec
