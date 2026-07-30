from pydantic import BaseModel
from typing import Literal, Optional

class UserResponse(BaseModel):
    id: str
    email: Optional[str]
    name: Optional[str]
    role: Optional[Literal["tinh", "xa"]] = None
    commune_id: Optional[int]

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[Literal["tinh", "xa"]] = None
    commune_id: Optional[int] = None
