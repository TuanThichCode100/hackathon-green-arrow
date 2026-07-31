import json

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.communes.models import Commune, Hamlet
from app.modules.residents.models import Resident


def _commune_response(commune: Commune, population: int) -> dict:
    """Build the public commune projection from the resident registry."""
    return {
        "id": commune.id,
        "name": commune.name,
        "lat": commune.lat,
        "lng": commune.lng,
        "population": int(population or 0),
        "notification_status": commune.notification_status,
        "disaster_type": getattr(commune, "disaster_type", None),
        "disaster_icon": getattr(commune, "disaster_icon", None),
        "alert_status": getattr(commune, "alert_status", None),
        "recv_rate": getattr(commune, "recv_rate", None),
    }


def list_communes(db: Session, status_filter: str | None = None):
    population = func.count(Resident.id).label("population")
    query = db.query(Commune, population).outerjoin(
        Resident, Resident.commune_id == Commune.id
    )
    if status_filter:
        query = query.filter(Commune.notification_status == status_filter)

    rows = query.group_by(Commune.id).order_by(Commune.name).all()
    return [_commune_response(commune, count) for commune, count in rows]


def get_commune(db: Session, commune_id: int):
    population = func.count(Resident.id).label("population")
    row = (
        db.query(Commune, population)
        .outerjoin(Resident, Resident.commune_id == Commune.id)
        .filter(Commune.id == commune_id)
        .group_by(Commune.id)
        .first()
    )
    if not row:
        return None
    commune, count = row
    return _commune_response(commune, count)


def get_hamlets(db: Session, commune_id: int):
    return db.query(Hamlet).filter(Hamlet.commune_id == commune_id).all()


def seed_communes(db: Session):
    if db.query(Commune).count() > 0:
        return
    try:
        with open("data/communes_seed.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            for index, item in enumerate(data):
                commune = Commune(
                    id=index + 1,
                    name=item["name"],
                    lat=item.get("lat", 0.0),
                    lng=item.get("lng", 0.0),
                    # Population is projected from residents; seed values are not operational data.
                    population=0,
                )
                db.add(commune)
                db.commit()
                db.refresh(commune)
                for hamlet_data in item.get("hamlets", []):
                    db.add(Hamlet(
                        commune_id=commune.id,
                        name=hamlet_data["name"],
                        headman_name=hamlet_data.get("headman"),
                        headman_phone=hamlet_data.get("phone", "0987654321"),
                        population=hamlet_data.get("population", 0),
                    ))
            db.commit()
    except Exception as exc:
        print("Seed error:", exc)
