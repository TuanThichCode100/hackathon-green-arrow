from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import json

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Response, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.common.schemas import APIResponse
from app.core.auth import get_current_user_metadata, require_role
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.dependencies import get_db
from app.modules.documents import schemas, service
from app.modules.documents.models import Document, DocumentAuditEvent, DocumentViewRequest

router = APIRouter(prefix="/api/documents", tags=["Documents"])
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png"}


def get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Không tìm thấy văn bản")
    return document


@router.get("", response_model=APIResponse[list[schemas.DocumentResponse]])
def get_docs(status: str | None = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    return {"data": service.list_documents(db, user, status)}


@router.get("/activity", response_model=APIResponse[list[dict]])
def document_activity(db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    events = db.query(DocumentAuditEvent).order_by(DocumentAuditEvent.created_at.desc()).limit(30).all()
    visible = []
    for event in events:
        document = db.query(Document).filter(Document.id == event.document_id).first()
        if not document or document.upload_status not in {"approved", "deleted"}:
            continue
        visible.append({"id": event.id, "actor_name": event.actor_name, "actor_role": event.actor_role, "action": event.action, "document_id": event.document_id, "document_title": document.title, "created_at": event.created_at})
    return {"data": visible}


@router.post("/upload", response_model=APIResponse[schemas.DocumentResponse])
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh"]))):
    content = await file.read()
    extension = Path(file.filename or "").suffix.lower()
    if not content:
        raise HTTPException(status_code=422, detail="Tệp tải lên đang trống")
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="Tệp vượt quá giới hạn 20 MB")
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Chỉ hỗ trợ PDF, DOCX, TXT, JPG hoặc PNG")
    key = service.storage_key("originals", extension.lstrip("."))
    service.save_encrypted(key, content)
    document = Document(code=f"DRAFT-{hashlib.sha256(content).hexdigest()[:8].upper()}", title="Đang phân tích", doc_type="Chỉ đạo", issued_by="Chưa xác định", file_path=key, start_date=datetime.utcnow().date(), end_date=datetime.utcnow().date(), status="draft", upload_status="processing", source_hash=hashlib.sha256(content).hexdigest(), original_filename=file.filename, original_mime_type=file.content_type, uploaded_by=str(user.get("sub")), uploaded_by_name=service.actor_name(user), draft_expires_at=datetime.utcnow() + timedelta(hours=settings.DOCUMENT_DRAFT_TTL_HOURS))
    db.add(document); db.flush(); service.audit(db, document.id, user, "uploaded"); db.commit(); db.refresh(document)
    background_tasks.add_task(service.process_document, document.id, SessionLocal)
    return {"data": document}


@router.get("/{document_id}", response_model=APIResponse[schemas.DocumentResponse])
def get_document(document_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    document = get_document_or_404(db, document_id)
    if document.upload_status in {"processing", "pending_review", "failed"} and not service.can_manage_draft(document, user):
        raise HTTPException(status_code=403, detail="Không có quyền xem bản nháp")
    return {"data": document}


@router.get("/{document_id}/preview", response_model=APIResponse[schemas.DocumentPreviewResponse])
def preview(document_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    document = get_document_or_404(db, document_id)
    if not service.can_manage_draft(document, user):
        raise HTTPException(status_code=403, detail="Chỉ người upload mới xem được bản nháp")
    if document.upload_status == "processing":
        return JSONResponse(status_code=202, content={"data": {"status": "processing", "document_id": document.id}})
    analysis = service.read_draft(document)
    if document.upload_status == "failed":
        raise HTTPException(status_code=422, detail=analysis.get("error", "Không thể trích xuất văn bản"))
    return {"data": {"document": document, "draft": analysis.get("draft", {}), "evidence": analysis.get("evidence", {}), "extraction_confidence": analysis.get("extraction_confidence")}}


@router.put("/{document_id}/preview", response_model=APIResponse[schemas.DocumentPreviewResponse])
def update_preview(document_id: int, draft: schemas.DocumentDraft, db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    document = get_document_or_404(db, document_id)
    if not service.can_manage_draft(document, user):
        raise HTTPException(status_code=403, detail="Không có quyền sửa bản nháp")
    analysis = service.read_draft(document); analysis["draft"] = draft.model_dump(mode="json"); service.delete_object(document.draft_analysis_path); service.write_draft(document, analysis); service.audit(db, document.id, user, "draft_updated"); db.commit()
    return {"data": {"document": document, "draft": analysis["draft"], "evidence": analysis.get("evidence", {}), "extraction_confidence": analysis.get("extraction_confidence")}}


@router.post("/{document_id}/approve", response_model=APIResponse[schemas.DocumentResponse])
def approve(document_id: int, draft: schemas.DocumentDraft, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh"]))):
    document = get_document_or_404(db, document_id)
    if not service.can_manage_draft(document, user):
        raise HTTPException(status_code=403, detail="Không có quyền xác nhận bản nháp này")
    payload = draft.model_dump(mode="python"); service.validate_approval(payload); service.apply_draft(document, payload)
    service.delete_object(document.draft_analysis_path); document.draft_analysis_path = None; document.draft_expires_at = None; document.upload_status = "approved"; document.status = "active"; document.code = payload["document_number"]
    service.audit(db, document.id, user, "approved"); db.commit(); db.refresh(document)
    return {"data": document}


@router.post("/{document_id}/cancel", response_model=APIResponse[bool])
def cancel(document_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    document = get_document_or_404(db, document_id)
    if not service.can_manage_draft(document, user):
        raise HTTPException(status_code=403, detail="Không có quyền hủy bản nháp")
    service.delete_object(document.file_path); service.delete_object(document.draft_analysis_path); db.delete(document); db.commit()
    return {"data": True}


@router.post("/{document_id}/delete", response_model=APIResponse[schemas.DocumentResponse])
def soft_delete(document_id: int, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh"]))):
    document = get_document_or_404(db, document_id)
    if document.upload_status != "approved": raise HTTPException(status_code=409, detail="Chỉ xóa được văn bản đã duyệt")
    document.upload_status = "deleted"; document.deleted_at = datetime.utcnow(); document.deleted_by = str(user.get("sub")); document.deleted_by_name = service.actor_name(user); service.audit(db, document.id, user, "deleted"); db.commit(); return {"data": document}


@router.post("/{document_id}/restore", response_model=APIResponse[schemas.DocumentResponse])
def restore(document_id: int, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh"]))):
    document = get_document_or_404(db, document_id)
    if document.upload_status != "deleted": raise HTTPException(status_code=409, detail="Văn bản không ở trạng thái đã xóa")
    document.upload_status = "approved"; document.deleted_at = None; document.deleted_by = None; document.deleted_by_name = None; service.audit(db, document.id, user, "restored"); db.commit(); return {"data": document}


@router.post("/{document_id}/view-requests", response_model=APIResponse[dict])
def request_original(document_id: int, body: schemas.OriginalViewRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    document = get_document_or_404(db, document_id)
    if document.upload_status != "approved": raise HTTPException(status_code=404, detail="Không tìm thấy văn bản đã duyệt")
    request = DocumentViewRequest(document_id=document.id, requester_id=str(user.get("sub")), requester_name=service.actor_name(user), requester_role=user.get("role"), reason=body.reason, status="pending", expires_at=datetime.utcnow() + timedelta(hours=24)); db.add(request); service.audit(db, document.id, user, "original_requested"); db.commit(); return {"data": {"id": request.id, "status": request.status}}


@router.post("/view-requests/{request_id}/decision", response_model=APIResponse[dict])
def decide_original_request(request_id: int, body: schemas.OriginalViewDecision, db: Session = Depends(get_db), user: dict = Depends(require_role(["tinh"]))):
    request = db.query(DocumentViewRequest).filter(DocumentViewRequest.id == request_id).first()
    if not request or request.status != "pending" or request.expires_at < datetime.utcnow():
        raise HTTPException(status_code=404, detail="Yêu cầu xem không còn hiệu lực")
    request.status = "approved" if body.approve else "rejected"; request.approved_by = str(user.get("sub")); request.approved_at = datetime.utcnow(); request.view_expires_at = datetime.utcnow() + timedelta(hours=24) if body.approve else None
    service.audit(db, request.document_id, user, "original_view_approved" if body.approve else "original_view_rejected", {"request_id": request.id}); db.commit()
    return {"data": {"id": request.id, "status": request.status, "view_expires_at": request.view_expires_at}}


@router.get("/{document_id}/original")
def view_original(document_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    document = get_document_or_404(db, document_id)
    now = datetime.utcnow(); permitted = user.get("role") == "tinh" and document.show_original_to_province
    if not permitted:
        permitted = db.query(DocumentViewRequest).filter(DocumentViewRequest.document_id == document.id, DocumentViewRequest.requester_id == str(user.get("sub")), DocumentViewRequest.status == "approved", DocumentViewRequest.view_expires_at > now).first() is not None
    if not permitted:
        raise HTTPException(status_code=403, detail="Cần được phê duyệt để xem bản gốc")
    service.audit(db, document.id, user, "original_viewed"); db.commit()
    return Response(content=service.read_encrypted(document.file_path), media_type=document.original_mime_type or "application/octet-stream", headers={"Content-Disposition": "inline"})
