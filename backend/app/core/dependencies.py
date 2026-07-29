from fastapi import HTTPException

from app.core.database import SessionLocal, check_database_connection

def get_db():
    if not check_database_connection():
        raise HTTPException(
            status_code=503,
            detail={"code": "DATA_CENTER_UNAVAILABLE", "message": "Mất kết nối tới trung tâm dữ liệu"},
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
