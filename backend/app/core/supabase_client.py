from fastapi import HTTPException
from supabase import Client, create_client

from app.core.config import settings


def get_supabase_admin() -> Client:
    """Create the privileged client only for requests that actually need it."""
    if not settings.SUPABASE_URL or not settings.supabase_admin_key:
        raise HTTPException(
            status_code=503,
            detail={"code": "DATA_CENTER_UNAVAILABLE", "message": "Mất kết nối tới trung tâm dữ liệu"},
        )
    return create_client(settings.SUPABASE_URL, settings.supabase_admin_key)
