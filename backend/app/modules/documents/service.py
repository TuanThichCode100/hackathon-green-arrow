from sqlalchemy.orm import Session
from app.modules.documents.models import Document

def list_documents(db: Session):
    return db.query(Document).order_by(Document.created_at.desc()).all()

def create_document(db: Session, doc_data: dict) -> Document:
    doc = Document(**doc_data)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc
