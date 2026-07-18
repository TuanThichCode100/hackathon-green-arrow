from fastapi import APIRouter, HTTPException, Depends
from app.common.schemas import APIResponse
from app.modules.auth import service, schemas
from app.core.auth import get_current_user_role

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login", response_model=APIResponse[schemas.LoginResponse])
def login(req: schemas.LoginRequest):
    user = service.verify_user(req.phone, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"data": {"token": "mock-jwt-token", "user": user}}

@router.get("/me", response_model=APIResponse[dict])
def get_me(role: str = Depends(get_current_user_role)):
    return {"data": {"role": role}}
