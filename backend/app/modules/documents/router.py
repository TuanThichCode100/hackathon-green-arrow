from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime
from cryptography.fernet import Fernet
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.documents import service, schemas
from app.core.auth import get_current_user_metadata, require_role
from app.core.supabase_client import get_supabase_admin
from app.core.config import settings

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.get("", response_model=APIResponse[List[schemas.DocumentResponse]])
def get_docs(db: Session = Depends(get_db), user: dict = Depends(get_current_user_metadata)):
    return {"data": service.list_documents(db)}

@router.post("/upload", response_model=APIResponse[schemas.DocumentResponse])
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    doc_type: str = Form("Chỉ đạo"),
    issued_by: str = Form("UBND Tỉnh"),
    start_date: str = Form(...),
    end_date: str = Form(...),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["tinh"]))
):
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=422, detail="Tệp tải lên đang trống")
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=422, detail="Tệp vượt quá giới hạn 20 MB")
        if not file.filename or file.filename.rsplit(".", 1)[-1].lower() not in {"pdf", "doc", "docx", "txt", "md"}:
            raise HTTPException(status_code=422, detail="Chỉ hỗ trợ tệp PDF, Word hoặc văn bản")
        
        # Mã hóa AES (Fernet)
        f = Fernet(settings.DOCUMENT_ENCRYPTION_KEY.encode('utf-8'))
        encrypted_content = f.encrypt(content)
        
        # Upload lên Supabase Storage
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
        file_name = f"{uuid.uuid4().hex}.{file_ext}.enc"
        analysis, summary = service.analyse_document(content, file.filename, title)

        # Prefer managed object storage in production, but provide a local,
        # encrypted fallback for the configured Docker volume and development.
        if settings.SUPABASE_URL and settings.supabase_admin_key:
            get_supabase_admin().storage.from_("documents").upload(
                file_name, encrypted_content, {"content-type": "application/octet-stream"}
            )
            file_path = file_name
        else:
            file_path = service.save_local_document(encrypted_content, analysis, file_name, settings.DOCUMENT_STORAGE_DIR)
        
        # Lưu Database
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        doc_data = {
            "code": f"DOC-{uuid.uuid4().hex[:6].upper()}",
            "title": title,
            "doc_type": doc_type,
            "issued_by": issued_by,
            "file_path": file_path,
            "llm_summary": summary,
            "start_date": s_date,
            "end_date": e_date,
            "status": "active"
        }
        
        doc = service.create_document(db, doc_data)
        return {"data": doc}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload: {str(e)}")
