import httpx
from fastapi import Depends, HTTPException, Request

from app.core.config import settings


def verify_supabase_token_online(token: str):
    """Verify a user session with Supabase without storing a local JWT secret."""
    try:
        response = httpx.get(
            f"{settings.SUPABASE_URL}/auth/v1/user",
            headers={"Authorization": f"Bearer {token}", "apikey": settings.supabase_api_key},
            timeout=5.0,
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def get_current_user_metadata(request: Request):
    """Resolve trusted server-managed access claims from the Supabase session."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không hợp lệ")

    user = verify_supabase_token_online(auth_header.split(" ", 1)[1])
    if not user:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn")

    email = (user.get("email") or "").strip().lower()
    allowed_domain = settings.ALLOWED_EMAIL_DOMAIN.strip().lower()
    if not email or not allowed_domain or not email.endswith(f"@{allowed_domain}"):
        raise HTTPException(status_code=403, detail="Tài khoản chưa được cấp quyền truy cập hệ thống")

    user_metadata = user.get("user_metadata") or {}
    app_metadata = user.get("app_metadata") or {}
    role = app_metadata.get("role")
    commune_id = app_metadata.get("commune_id")
    if role not in {"tinh", "xa"}:
        raise HTTPException(status_code=403, detail="Tài khoản chưa được cấp quyền truy cập hệ thống")
    if role == "xa" and not isinstance(commune_id, int):
        raise HTTPException(status_code=403, detail="Tài khoản chưa được gán xã/phường phụ trách")

    return {
        "role": role,
        "commune_id": commune_id,
        "sub": user.get("id"),
        "name": user_metadata.get("name") or email,
        "email": email,
    }


def get_current_user_role(metadata: dict = Depends(get_current_user_metadata)):
    return metadata.get("role")


def require_role(allowed_roles: list[str]):
    def role_checker(metadata: dict = Depends(get_current_user_metadata)):
        if metadata.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện thao tác này")
        return metadata

    return role_checker
