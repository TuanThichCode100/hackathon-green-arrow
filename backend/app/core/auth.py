import httpx
from fastapi import HTTPException, Depends, Request

from app.core.config import settings

def verify_supabase_token_online(token: str):
    """Verify the user session with Supabase without storing a local JWT signing secret."""
    try:
        resp = httpx.get(
            f"{settings.SUPABASE_URL}/auth/v1/user",
            headers={"Authorization": f"Bearer {token}", "apikey": settings.supabase_api_key},
            timeout=5.0
        )
        if resp.status_code == 200:
            user = resp.json()
            return user
    except Exception:
        pass
    return None

def get_current_user_metadata(request: Request):
    """Resolve the authenticated user's metadata from a Supabase access token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized: Missing or invalid token format")
    
    token = auth_header.split(" ")[1]
    
    user = verify_supabase_token_online(token)
    if user:
        meta = user.get("user_metadata", {})
        return {"role": meta.get("role", "tinh"), "commune_id": meta.get("commune_id"), "sub": user.get("id")}
    raise HTTPException(status_code=401, detail="Unauthorized: Invalid or expired token")

def get_current_user_role(metadata: dict = Depends(get_current_user_metadata)):
    return metadata.get("role")

def require_role(allowed_roles: list[str]):
    """
    Lớp bảo mật 3: Role-based Access Control (RBAC)
    """
    def role_checker(metadata: dict = Depends(get_current_user_metadata)):
        role = metadata.get("role")
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden: Insufficient permissions")
        return metadata
    return role_checker
