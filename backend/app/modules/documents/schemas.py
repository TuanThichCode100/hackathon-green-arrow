from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional

class DocumentResponse(BaseModel):
    id: int
    code: str
    title: str
    doc_type: str
    issued_by: str
    llm_summary: Optional[str]
    start_date: date
    end_date: date
    status: str
    model_config = ConfigDict(from_attributes=True)
