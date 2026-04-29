"""Authentication and user schemas."""
from pydantic import BaseModel
from typing import List, Optional


class UserLogin(BaseModel):
    email: str
    password: str


class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "READ_ONLY"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    roles: List[str] = []
    permissions: List[str] = []
    assigned_projects: List[str] = []
    is_impersonated: bool = False
    impersonated_by_name: Optional[str] = None

    class Config:
        from_attributes = True


class ImpersonateResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MicrosoftToken(BaseModel):
    id_token: str
