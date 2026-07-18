from fastapi import APIRouter, HTTPException, Depends
from app.common.schemas import APIResponse
from app.modules.auth import schemas
from app.core.auth import get_current_user_role

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# Login endpoint removed. Authentication is now handled directly by Supabase on the Frontend.

@router.get("/me", response_model=APIResponse[dict])
def get_me(role: str = Depends(get_current_user_role)):
    return {"data": {"role": role}}
