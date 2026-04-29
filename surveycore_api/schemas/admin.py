"""Admin schemas — gestión de usuarios, roles y permisos."""
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import date
import re


class AssignmentOut(BaseModel):
    id: int
    project_code: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    class Config:
        from_attributes = True


class AdminUserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    role_id: Optional[int] = None
    assignments: List[AssignmentOut]

    class Config:
        from_attributes = True


class SetRoleIn(BaseModel):
    role: str          # nombre del rol (ej. "SURVEY_MANAGER")


class AddAssignmentIn(BaseModel):
    project_code: str
    start_date: date
    end_date: Optional[date] = None


# ── Permisos ──────────────────────────────────────────────────────────────────

class PermissionOut(BaseModel):
    id: int
    code: str
    description: str

    class Config:
        from_attributes = True


# ── Roles ─────────────────────────────────────────────────────────────────────

class RoleDetailOut(BaseModel):
    role_id: int
    role_name: str
    description: Optional[str] = None
    permissions: List[str]           # lista de códigos de permiso
    user_count: int
    is_system: bool


class CreateRoleIn(BaseModel):
    role_name: str
    description: Optional[str] = None

    @field_validator("role_name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_]", "_", v.strip()).upper()
        if not cleaned:
            raise ValueError("role_name no puede estar vacío")
        return cleaned


class UpdateRoleIn(BaseModel):
    description: Optional[str] = None
    role_name: Optional[str] = None   # solo para roles no-sistema


class SetRolePermissionsIn(BaseModel):
    permissions: List[str]            # lista de códigos de permiso


# kept for internal use
class RolePermissionsOut(BaseModel):
    role_name: str
    permissions: List[str]


# ── Assignments (full CRUD) ───────────────────────────────────────────────────

class AssignmentDetailOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    project_code: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    class Config:
        from_attributes = True


class CreateAssignmentIn(BaseModel):
    user_id: int
    project_code: str
    start_date: date
    end_date: Optional[date] = None


class UpdateAssignmentIn(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
