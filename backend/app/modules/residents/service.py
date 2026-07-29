from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
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
    try:
        r = Resident(**data.model_dump())
        db.add(r)
        db.commit()
        db.refresh(r)
        return r
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Số điện thoại đã tồn tại trong danh sách dân cư")

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
    phones = [row["phone"] for row in records]
    if len(phones) != len(set(phones)):
        raise HTTPException(status_code=422, detail="CSV có số điện thoại trùng lặp")
    existing = db.query(Resident.phone).filter(Resident.phone.in_(phones)).first() if phones else None
    if existing:
        raise HTTPException(status_code=409, detail=f"Số điện thoại {existing[0]} đã tồn tại")
    try:
        db.add_all([Resident(**row) for row in records])
        db.commit()
        return len(records)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Không thể import vì có số điện thoại đã tồn tại")
