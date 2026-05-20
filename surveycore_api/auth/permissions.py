"""
RBAC permission dependency factory — usa joins normalizados (role_id, permission_id).

Uso en routers:
    @router.post("/surveys/")
    def create_survey(..., current_user: User = Depends(require_permission("survey.create"))):
"""
from typing import List, Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from typing import Optional

from ..dependencies import get_db
from ..models import User, Role, RolePermission, Permission, Assignment, Project
from .deps import get_current_user

VALID_ROLES = {"ADMIN", "SURVEY_MANAGER", "BASIC", "READ_ONLY"}


def get_user_permissions(user: User, db: Session) -> List[str]:
    """Devuelve todos los códigos de permiso del rol del usuario vía JOIN normalizado."""
    if not user.role_id:
        return []
    rows = (
        db.query(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(RolePermission.role_id == user.role_id)
        .all()
    )
    return [r.code for r in rows]


def get_user_project_ids(user: User, db: Session) -> List[int]:
    """
    Devuelve IDs de proyectos accesibles al usuario via:
    1. Tabla assignments (project.project_code = assignment.project_code where user.email)
    2. Email manager fields (client_manager_email, delivery_manager_email, project_head_email)
    ADMIN devuelve lista vacía — los callers deben saltar el filtro para ADMIN.
    """
    if user.role == "ADMIN":
        return []

    assignment_rows = (
        db.query(Project.id)
        .join(Assignment, Assignment.project_code == Project.project_code)
        .filter(Assignment.user_email == user.email)
        .distinct()
        .all()
    )

    email_rows = (
        db.query(Project.id)
        .filter(
            or_(
                Project.client_manager_email == user.email,
                Project.delivery_manager_email == user.email,
                Project.project_head_email == user.email,
            )
        )
        .all()
    )

    return list({r.id for r in assignment_rows} | {r.id for r in email_rows})


def get_user_assigned_projects(user: User, db: Session) -> List[str]:
    """Return project_codes accessible to the user (all for ADMIN)."""
    if user.role == "ADMIN":
        return [r.project_code for r in db.query(Project.project_code).distinct().all()]
    return [
        r.project_code
        for r in (
            db.query(Project.project_code)
            .join(Assignment, Assignment.project_code == Project.project_code)
            .filter(Assignment.user_email == user.email)
            .distinct()
            .all()
        )
    ]


def build_user_response(
    user: User,
    db: Session,
    imp_by_id: Optional[str] = None,
) -> dict:
    """Build the full /auth/me payload: permissions, project scope, impersonation meta."""
    impersonated_by_name: Optional[str] = None
    if imp_by_id:
        admin = db.get(User, int(imp_by_id))
        impersonated_by_name = admin.name if admin else None

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "roles": [user.role],
        "permissions": get_user_permissions(user, db),
        "assigned_projects": get_user_assigned_projects(user, db),
        "is_impersonated": imp_by_id is not None,
        "impersonated_by_name": impersonated_by_name,
    }


def require_permission(permission_code: str) -> Callable:
    """
    Factory de dependency FastAPI para control de acceso por permiso.
    Autentica el usuario y verifica que su rol tenga el permiso requerido.
    Lanza HTTP 403 si el permiso no está asignado al rol.
    """
    def _check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        permissions = get_user_permissions(current_user, db)
        if permission_code not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso '{permission_code}' requerido.",
            )
        return current_user

    return _check
