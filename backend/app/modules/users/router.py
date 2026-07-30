from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.common.schemas import APIResponse
from app.core.auth import require_role
from app.core.supabase_client import get_supabase_admin
from app.modules.users import schemas

router = APIRouter(prefix="/api/users", tags=["Users"])


def serialize_user(user):
    user_metadata = user.user_metadata or {}
    app_metadata = user.app_metadata or {}
    return {
        "id": user.id,
        "email": user.email,
        "name": user_metadata.get("name", "Người dùng"),
        "role": app_metadata.get("role"),
        "commune_id": app_metadata.get("commune_id"),
    }


@router.get("", response_model=APIResponse[List[schemas.UserResponse]])
def list_users(user: dict = Depends(require_role(["tinh"]))):
    try:
        response = get_supabase_admin().auth.admin.list_users()
        supabase_users = response if isinstance(response, list) else response.users
        return {"data": [serialize_user(item) for item in supabase_users]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Không thể tải danh sách tài khoản") from exc


@router.put("/{user_id}", response_model=APIResponse[schemas.UserResponse])
def update_user_role(
    user_id: str,
    data: schemas.UserUpdate,
    user: dict = Depends(require_role(["tinh"])),
):
    try:
        supabase_admin = get_supabase_admin()
        existing = supabase_admin.auth.admin.get_user_by_id(user_id).user
        user_metadata = existing.user_metadata or {}
        app_metadata = existing.app_metadata or {}

        if data.name is not None:
            user_metadata["name"] = data.name.strip()
        if data.role is not None:
            app_metadata["role"] = data.role
        if "commune_id" in data.model_fields_set:
            app_metadata["commune_id"] = data.commune_id

        effective_role = app_metadata.get("role")
        if effective_role == "xa" and not isinstance(app_metadata.get("commune_id"), int):
            raise HTTPException(status_code=422, detail="Cán bộ xã phải được gán xã/phường phụ trách")
        if effective_role == "tinh":
            app_metadata["commune_id"] = None

        response = supabase_admin.auth.admin.update_user_by_id(
            user_id,
            {"user_metadata": user_metadata, "app_metadata": app_metadata},
        )
        return {"data": serialize_user(response.user)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Không thể cập nhật quyền tài khoản") from exc
