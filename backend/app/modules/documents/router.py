from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db
from app.common.schemas import APIResponse
from app.modules.documents import service, schemas

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.get("", response_model=APIResponse[List[schemas.DocumentResponse]])
def get_docs(db: Session = Depends(get_db)):
    return {"data": service.list_documents(db)}
