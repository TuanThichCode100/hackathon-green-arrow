import os
import json
from sqlalchemy.orm import Session
from app.modules.agent.models import AgentDecision
from app.modules.communes.models import Commune
from app.modules.documents.models import Document
from google import genai
from google.genai import types

def get_decisions(db: Session, page: int = 1, limit: int = 50):
    return db.query(AgentDecision).order_by(AgentDecision.created_at.desc()).offset((page-1)*limit).limit(limit).all()

def draft_bulletin(db: Session, request):
    # Get communes
    communes = db.query(Commune).filter(Commune.id.in_(request.commune_ids)).all()
    commune_info = [f"- Xã {c.name} (Dân số: {c.population}, Tọa độ: {c.lat}, {c.lng})" for c in communes]
    
    # Get recent documents for context (RAG fallback)
    docs = db.query(Document).filter(Document.status == "active", Document.upload_status == "approved").limit(3).all()
    doc_info = [f"- {d.title}: {d.llm_summary or 'Không có tóm tắt'}" for d in docs]

    prompt = f"""
Bạn là một AI Agent phân tích thời tiết và sinh bản tin cảnh báo khẩn cấp cho tỉnh Điện Biên.
Loại thiên tai: {request.disaster_type}

Dữ liệu các xã bị ảnh hưởng:
{chr(10).join(commune_info)}

Chỉ đạo từ cơ quan ban ngành (RAG):
{chr(10).join(doc_info)}

Dựa vào thông tin trên, hãy sinh ra bản tin cảnh báo gửi đến người dân. 
Yêu cầu trả về BẮT BUỘC theo format JSON sau:
{{
    "severity": "watch|alert",
    "bulletin_text": "Nội dung văn bản tiếng Việt chi tiết",
    "audio_tags": "tag1,tag2" // ví dụ: "canh_bao_lu,xa_muong_pon"
}}
"""

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        result_json = {
            "severity": "alert",
            "bulletin_text": f"[DEMO] BẢN TIN CẢNH BÁO {request.disaster_type.upper()}.\nĐây là bản tin giả lập vì chưa cấu hình GEMINI_API_KEY trong .env",
            "audio_tags": "canh_bao,di_tan"
        }
    else:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            result_json = json.loads(response.text)
        except Exception as e:
            result_json = {
                "severity": "watch",
                "bulletin_text": f"Lỗi sinh bản tin: {str(e)}",
                "audio_tags": "error"
            }

    dec = AgentDecision(
        trigger_type="ai_draft",
        reasoning=f"Sinh bản tin tự động cho {request.disaster_type}",
        actions_json="[]",
        communes_affected=",".join(map(str, request.commune_ids)),
        bulletin_text=result_json.get("bulletin_text", ""),
        audio_tags=result_json.get("audio_tags", ""),
        severity=result_json.get("severity", ""),
        status="draft"
    )
    db.add(dec)
    db.commit()
    db.refresh(dec)
    return dec

def approve_bulletin(db: Session, decision_id: int):
    dec = db.query(AgentDecision).filter(AgentDecision.id == decision_id).first()
    if dec:
        dec.status = "approved"
        dec.actions_json = json.dumps([
            {"type": "zalo", "status": "sent", "time": "now"},
            {"type": "tts_loa", "status": "sent", "time": "now"}
        ])
        db.commit()
        db.refresh(dec)
    return dec

from app.modules.notifications.models import Notification

def manual_trigger(db: Session, request):
    # Lấy thông điệp
    message = request.message if hasattr(request, 'message') else "Cảnh báo khẩn cấp"
    
    dec = AgentDecision(
        trigger_type="manual_trigger",
        reasoning="Cán bộ kích hoạt thủ công",
        actions_json=json.dumps([{"type": "zalo", "status": "sent"}, {"type": "sms", "status": "sent"}]),
        communes_affected=",".join(map(str, request.commune_ids)),
        status="executing"
    )
    db.add(dec)
    db.commit()
    db.refresh(dec)
    
    # Tạo notifications thật
    for cid in request.commune_ids:
        for channel in ["zalo", "sms", "loa"]:
            notif = Notification(
                commune_id=cid,
                decision_id=dec.id,
                channel=channel,
                ethnic_language="Kinh",
                content=f"[{request.disaster_type}] {message}",
                recipient_count=100, # Giả lập 100 người
                status="delivered"
            )
            db.add(notif)
    
    db.commit()
    return dec
