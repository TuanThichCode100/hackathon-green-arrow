import json
import os

from google import genai
from google.genai import types
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.agent.models import AgentDecision
from app.modules.communes.models import Commune
from app.modules.documents.models import Document
from app.modules.notifications import service as notification_service
from app.modules.residents.models import Resident


def get_decisions(db: Session, page: int = 1, limit: int = 50):
    return (
        db.query(AgentDecision)
        .order_by(AgentDecision.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )


def draft_bulletin(db: Session, request):
    communes = db.query(Commune).filter(Commune.id.in_(request.commune_ids)).all()
    resident_counts = dict(
        db.query(Resident.commune_id, func.count(Resident.id))
        .filter(Resident.commune_id.in_(request.commune_ids))
        .group_by(Resident.commune_id)
        .all()
    )
    commune_info = [
        f"- Xã/phường {commune.name} (dân số: {resident_counts.get(commune.id, 0)}, tọa độ: {commune.lat}, {commune.lng})"
        for commune in communes
    ]
    docs = (
        db.query(Document)
        .filter(Document.status == "active", Document.upload_status == "approved")
        .limit(3)
        .all()
    )
    doc_info = [f"- {document.title}: {document.llm_summary or 'Chưa có tóm tắt'}" for document in docs]

    prompt = f"""
Bạn là trợ lý soạn bản tin cảnh báo khẩn cấp cho tỉnh Điện Biên.
Loại thiên tai: {request.disaster_type}

Địa bàn bị ảnh hưởng:
{chr(10).join(commune_info)}

Văn bản chỉ đạo liên quan:
{chr(10).join(doc_info)}

Chỉ trả về JSON có các khóa severity (watch|alert), bulletin_text (tiếng Việt), và audio_tags.
"""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        result_json = {
            "severity": "alert",
            "bulletin_text": f"[DEMO] Cảnh báo {request.disaster_type.upper()}.",
            "audio_tags": "canh_bao,di_tan",
        }
    else:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            result_json = json.loads(response.text)
        except Exception as exc:
            result_json = {
                "severity": "watch",
                "bulletin_text": f"Không thể tạo bản tin: {exc}",
                "audio_tags": "error",
            }

    decision = AgentDecision(
        trigger_type="ai_draft",
        reasoning=f"Tạo bản tin tự động cho {request.disaster_type}",
        actions_json="[]",
        communes_affected=",".join(map(str, request.commune_ids)),
        bulletin_text=result_json.get("bulletin_text", ""),
        audio_tags=result_json.get("audio_tags", ""),
        severity=result_json.get("severity", ""),
        status="draft",
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


def approve_bulletin(db: Session, decision_id: int):
    decision = db.query(AgentDecision).filter(AgentDecision.id == decision_id).first()
    if decision:
        decision.status = "approved"
        decision.actions_json = json.dumps([
            {"type": "zalo", "status": "sent", "time": "now"},
            {"type": "tts_loa", "status": "sent", "time": "now"},
        ])
        db.commit()
        db.refresh(decision)
    return decision


def manual_trigger(db: Session, request):
    message = request.message if getattr(request, "message", None) else "Cảnh báo khẩn cấp"
    decision = AgentDecision(
        trigger_type="manual_trigger",
        reasoning="Cán bộ kích hoạt thủ công",
        actions_json=json.dumps([
            {"type": "zalo", "status": "pending"},
            {"type": "sms", "status": "pending"},
        ]),
        communes_affected=",".join(map(str, request.commune_ids)),
        status="executing",
    )
    db.add(decision)
    db.flush()

    for commune_id in request.commune_ids:
        for channel in ["zalo", "sms", "loa"]:
            notification_service.create_language_dispatches(
                db,
                commune_id=commune_id,
                decision_id=decision.id,
                channel=channel,
                vietnamese_content=f"[{request.disaster_type}] {message}",
            )

    db.commit()
    db.refresh(decision)
    return decision
