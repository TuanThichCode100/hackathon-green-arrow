from pydantic import BaseModel
from typing import Optional

class UserResponse(BaseModel):
    id: str
    email: Optional[str]
    name: Optional[str]
    role: str
    commune_id: Optional[int]

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    commune_id: Optional[int] = None
