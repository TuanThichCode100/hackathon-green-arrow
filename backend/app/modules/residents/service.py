from sqlalchemy.orm import Session
from app.modules.residents.models import Resident

def list_residents(db: Session, commune_id: int = None, ethnic: str = None, skip: int = 0, limit: int = 50):
    q = db.query(Resident)
    if commune_id:
        q = q.filter(Resident.commune_id == commune_id)
    if ethnic:
        q = q.filter(Resident.ethnic == ethnic)
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return total, items

def create_resident(db: Session, data):
    r = Resident(**data.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r
