import re

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.residents.models import Resident
from app.modules.communes.models import Commune
from app.modules.residents.languages import primary_language_for


PHONE_PATTERN = re.compile(r"^0\d{9}$")


def list_residents(db: Session, commune_id: int = None, ethnic: str = None, skip: int = 0, limit: int = 50):
    query = db.query(Resident)
    if commune_id:
        query = query.filter(Resident.commune_id == commune_id)
    if ethnic:
        query = query.filter(Resident.ethnic == ethnic)
    return query.count(), query.offset(skip).limit(limit).all()


def create_resident(db: Session, data):
    try:
        values = data.model_dump()
        values["primary_language"] = primary_language_for(values["ethnic"], values.get("primary_language"))
        resident = Resident(**values)
        db.add(resident)
        db.commit()
        db.refresh(resident)
        return resident
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Số điện thoại đã tồn tại trong danh sách dân cư")


def get_resident(db: Session, resident_id: int, commune_id: int | None = None):
    query = db.query(Resident).filter(Resident.id == resident_id)
    if commune_id is not None:
        query = query.filter(Resident.commune_id == commune_id)
    return query.first()


def update_resident(
    db: Session,
    resident_id: int,
    data,
    commune_id: int | None = None,
    allow_commune_change: bool = False,
):
    resident = get_resident(db, resident_id, commune_id)
    if resident:
        update_data = data.model_dump(exclude_unset=True)
        if not allow_commune_change:
            update_data.pop("commune_id", None)
        if "commune_id" in update_data and not db.query(Commune.id).filter(Commune.id == update_data["commune_id"]).first():
            raise HTTPException(status_code=422, detail="Xã/phường được chọn không còn trong danh mục hiện hành")
        if "ethnic" in update_data or "primary_language" in update_data:
            update_data["primary_language"] = primary_language_for(
                update_data.get("ethnic", resident.ethnic), update_data.get("primary_language")
            )
        changed = {key: value for key, value in update_data.items() if getattr(resident, key) != value}
        if not changed:
            raise HTTPException(status_code=422, detail="Chưa có thông tin nào thay đổi để lưu")
        for key, value in changed.items():
            setattr(resident, key, value)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Số điện thoại đã tồn tại trong danh sách dân cư")
        db.refresh(resident)
    return resident


def delete_resident(db: Session, resident_id: int, commune_id: int | None = None):
    resident = get_resident(db, resident_id, commune_id)
    if resident:
        db.delete(resident)
        db.commit()
        return True
    return False


def import_residents(db: Session, records: list[dict]):
    """Import valid CSV rows and return per-row issues without discarding the batch."""
    communes = db.query(Commune.id, Commune.name).all()
    commune_ids = {commune_id for commune_id, _ in communes}
    commune_names = {
        re.sub(r"\s+", " ", name.strip()).casefold(): commune_id
        for commune_id, name in communes
    }
    normalized_phones = [re.sub(r"\s+", "", row.get("phone", "")) for row in records]
    existing_phones = {
        phone for (phone,) in db.query(Resident.phone).filter(Resident.phone.in_(normalized_phones))
    } if normalized_phones else set()
    accepted, errors, accepted_phones = [], [], set()

    for index, row in enumerate(records, start=2):
        source_row = row.get("source_row") or index
        name = (row.get("name") or "").strip()
        phone = re.sub(r"\s+", "", row.get("phone") or "")
        ethnic = (row.get("ethnic") or "").strip()
        commune_id = row.get("commune_id")
        commune_name = re.sub(r"\s+", " ", (row.get("commune_name") or "").strip()).casefold()
        if commune_id is None and commune_name:
            commune_id = commune_names.get(commune_name)

        if commune_id is None:
            errors.append({"row": source_row, "reason": "Chưa có xã/phường cho bản ghi này."})
        elif commune_id not in commune_ids:
            errors.append({"row": source_row, "reason": "Xã/phường không tồn tại trong danh mục hiện hành."})
        elif len(name) < 2:
            errors.append({"row": source_row, "reason": "Họ và tên cần có ít nhất 2 ký tự."})
        elif not PHONE_PATTERN.fullmatch(phone):
            errors.append({"row": source_row, "reason": "Số điện thoại phải có 10 chữ số và bắt đầu bằng 0."})
        elif not ethnic:
            errors.append({"row": source_row, "reason": "Chưa có thông tin dân tộc."})
        elif phone in existing_phones:
            errors.append({"row": source_row, "reason": "Số điện thoại đã tồn tại trong danh sách dân cư."})
        elif phone in accepted_phones:
            errors.append({"row": source_row, "reason": "Số điện thoại bị trùng trong tệp CSV."})
        else:
            accepted_phones.add(phone)
            accepted.append({"commune_id": commune_id, "name": name, "phone": phone, "ethnic": ethnic, "primary_language": primary_language_for(ethnic, (row.get("primary_language") or "").strip()), "literate": bool(row.get("literate", True))})

    try:
        if accepted:
            db.add_all([Resident(**row) for row in accepted])
            db.commit()
        return {"imported": len(accepted), "skipped": len(errors), "errors": errors}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Không thể hoàn tất import vì dữ liệu đã thay đổi. Hãy kiểm tra và thử lại.")
