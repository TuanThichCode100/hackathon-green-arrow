from sqlalchemy.orm import Session
from app.modules.documents.models import Document
import json
import re
from io import BytesIO
from pathlib import Path
from datetime import datetime


def analyse_document(content: bytes, filename: str, title: str) -> tuple[dict, str]:
    """Create a deterministic, inspectable analysis for an uploaded document.

    This is deliberately independent of an external LLM so that an upload is
    still useful when an AI provider is unavailable.  Binary formats retain
    metadata while .txt documents also provide an extract and key sentences.
    """
    extension = Path(filename).suffix.lower()
    is_text = extension in {".txt", ".csv", ".md"}
    text = content.decode("utf-8", errors="replace") if is_text else ""
    extraction_note = None
    if extension == ".pdf":
        try:
            from pypdf import PdfReader
            text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
        except Exception:
            extraction_note = "Không thể trích nội dung PDF; tệp vẫn được lưu mã hóa cùng siêu dữ liệu."
    elif extension == ".docx":
        try:
            from docx import Document as WordDocument
            text = "\n".join(paragraph.text for paragraph in WordDocument(BytesIO(content)).paragraphs)
        except Exception:
            extraction_note = "Không thể trích nội dung DOCX; tệp vẫn được lưu mã hóa cùng siêu dữ liệu."
    elif extension == ".doc":
        extraction_note = "Định dạng DOC cũ chưa hỗ trợ trích nội dung; tệp vẫn được lưu mã hóa cùng siêu dữ liệu."
    normalized = " ".join(text.split())
    date_matches = re.findall(r"\b(?:0?[1-9]|[12]\d|3[01])[-/](?:0?[1-9]|1[0-2])[-/]\d{4}\b", normalized)
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]
    keywords = [word for word in ("khẩn", "sơ tán", "mưa", "lũ", "sạt lở", "cảnh báo") if word in normalized.lower()]
    analysis = {
        "version": 1,
        "source": {"filename": filename, "title": title, "size_bytes": len(content), "content_type": "text" if text else "binary"},
        "analysed_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "extract": normalized[:4000] if normalized else None,
        "dates_detected": date_matches,
        "keywords_detected": keywords,
        "key_sentences": sentences[:5],
        "note": extraction_note or (None if text else "Tệp nhị phân đã được lưu cùng siêu dữ liệu."),
    }
    summary = sentences[0][:500] if sentences else f"Đã tiếp nhận {filename}; thông tin tệp và kết quả phân tích được lưu kèm văn bản."
    return analysis, summary


def save_local_document(encrypted_content: bytes, analysis: dict, storage_name: str, storage_dir: str) -> str:
    directory = Path(storage_dir)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / storage_name).write_bytes(encrypted_content)
    (directory / f"{storage_name}.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    return storage_name

def list_documents(db: Session):
    return db.query(Document).order_by(Document.created_at.desc()).all()

def create_document(db: Session, doc_data: dict) -> Document:
    doc = Document(**doc_data)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc
