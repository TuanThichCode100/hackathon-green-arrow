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

def update_resident(db: Session, resident_id: int, data):
    r = db.query(Resident).filter(Resident.id == resident_id).first()
    if r:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(r, key, value)
        db.commit()
        db.refresh(r)
    return r

def delete_resident(db: Session, resident_id: int):
    r = db.query(Resident).filter(Resident.id == resident_id).first()
    if r:
        db.delete(r)
        db.commit()
        return True
    return False

def import_csv(db: Session, records: list):
    count = 0
    for row in records:
        r = Resident(**row)
        db.add(r)
        count += 1
    db.commit()
    return count
