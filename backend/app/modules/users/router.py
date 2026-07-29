from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.common.schemas import APIResponse
from app.modules.users import schemas
from app.core.auth import require_role
from app.core.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("", response_model=APIResponse[List[schemas.UserResponse]])
def list_users(user: dict = Depends(require_role(["tinh"]))):
    try:
        response = get_supabase_admin().auth.admin.list_users()
        supabase_users = response if isinstance(response, list) else response.users
        users = []
        for u in supabase_users:
            meta = u.user_metadata or {}
            users.append({
                "id": u.id,
                "email": u.email,
                "name": meta.get("name", "Người dùng"),
                "role": meta.get("role", "tinh"),
                "commune_id": meta.get("commune_id")
            })
        return {"data": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy danh sách user: {str(e)}")

@router.put("/{user_id}", response_model=APIResponse[schemas.UserResponse])
def update_user_role(user_id: str, data: schemas.UserUpdate, user: dict = Depends(require_role(["tinh"]))):
    try:
        supabase_admin = get_supabase_admin()
        # Get existing metadata to merge
        existing_user = supabase_admin.auth.admin.get_user_by_id(user_id)
        meta = existing_user.user.user_metadata or {}
        
        if data.name is not None: meta["name"] = data.name
        if data.role is not None: meta["role"] = data.role
        if data.commune_id is not None: meta["commune_id"] = data.commune_id
        
        response = supabase_admin.auth.admin.update_user_by_id(
            user_id,
            {"user_metadata": meta}
        )
        u = response.user
        new_meta = u.user_metadata or {}
        return {"data": {
            "id": u.id,
            "email": u.email,
            "name": new_meta.get("name", "Người dùng"),
            "role": new_meta.get("role", "tinh"),
            "commune_id": new_meta.get("commune_id")
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật user: {str(e)}")
