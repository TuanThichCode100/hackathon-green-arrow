import json
from sqlalchemy.orm import Session
from app.modules.communes.models import Commune, Hamlet

def list_communes(db: Session, status_filter: str = None):
    q = db.query(Commune)
    if status_filter:
        q = q.filter(Commune.notification_status == status_filter)
    return q.all()

def get_commune(db: Session, commune_id: int):
    return db.query(Commune).filter(Commune.id == commune_id).first()

def get_hamlets(db: Session, commune_id: int):
    return db.query(Hamlet).filter(Hamlet.commune_id == commune_id).all()

def seed_communes(db: Session):
    if db.query(Commune).count() > 0:
        return
    try:
        with open("data/communes_seed.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            for i, c in enumerate(data):
                comm = Commune(
                    id=i+1,
                    name=c["name"],
                    lat=c.get("lat", 0.0),
                    lng=c.get("lng", 0.0),
                    population=c.get("population", 0)
                )
                db.add(comm)
                db.commit()
                db.refresh(comm)
                for h in c.get("hamlets", []):
                    hamlet = Hamlet(
                        commune_id=comm.id,
                        name=h["name"],
                        headman_name=h.get("headman"),
                        headman_phone=h.get("phone", "0987654321"),
                        population=h.get("population", 0)
                    )
                    db.add(hamlet)
            db.commit()
    except Exception as e:
        print("Seed error:", e)
