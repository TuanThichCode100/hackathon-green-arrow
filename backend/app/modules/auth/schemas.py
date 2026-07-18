from pydantic import BaseModel

class LoginRequest(BaseModel):
    phone: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    role: str
    commune_id: int = None

class LoginResponse(BaseModel):
    token: str
    user: UserResponse
