from sqlalchemy.orm import Session
from app.modules.documents.models import Document

def list_documents(db: Session):
    return db.query(Document).order_by(Document.created_at.desc()).all()
