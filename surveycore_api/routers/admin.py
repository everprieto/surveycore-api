"""Admin router — CRUD de usuarios, roles y permisos."""
from collections import defaultdict
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List

from ..dependencies import get_db
from ..models import User, Assignment, Permission, Role, RolePermission, Project
from ..schemas.admin import (
    AdminUserOut, AssignmentOut, SetRoleIn, AddAssignmentIn,
    PermissionOut, RoleDetailOut, CreateRoleIn, UpdateRoleIn, SetRolePermissionsIn,
    AssignmentDetailOut, CreateAssignmentIn, UpdateAssignmentIn,
)
from ..schemas.auth import ImpersonateResponse, UserResponse
from ..auth.permissions import require_permission, build_user_response
from ..auth.jwt_handler import create_access_token

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _role_detail(role: Role, db: Session) -> RoleDetailOut:
    perms = (
        db.query(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(RolePermission.role_id == role.id)
        .all()
    )
    user_count = db.query(User).filter(User.role_id == role.id).count()
    return RoleDetailOut(
        role_id=role.id,
        role_name=role.name,
        description=role.description,
        permissions=[p.code for p in perms],
        user_count=user_count,
        is_system=role.is_system,
    )


def _get_role_or_404(role_id: int, db: Session) -> Role:
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return role


# ── Usuarios ──────────────────────────────────────────────────────────────────

@router.get("/users", response_model=List[AdminUserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.manage")),
):
    users = db.query(User).order_by(User.name).all()

    # Batch load all assignments in one query instead of N queries
    emails = [u.email for u in users if u.email]
    all_assignments = (
        db.query(Assignment).filter(Assignment.user_email.in_(emails)).all()
        if emails else []
    )
    assignments_by_email: dict[str, list] = defaultdict(list)
    for a in all_assignments:
        assignments_by_email[a.user_email].append(a)

    return [
        AdminUserOut(
            id=u.id, name=u.name, email=u.email,
            role=u.role or "", role_id=u.role_id,
            assignments=[AssignmentOut.model_validate(a) for a in assignments_by_email[u.email]],
        )
        for u in users
    ]


@router.put("/users/{user_id}/role", response_model=AdminUserOut)
def set_user_role(
    user_id: int,
    data: SetRoleIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.manage")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    role = db.query(Role).filter(Role.name == data.role).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Rol '{data.role}' no existe")

    user.role_id = role.id
    db.commit()
    db.refresh(user)

    assignments = db.query(Assignment).filter(Assignment.user_email == user.email).all()
    return AdminUserOut(
        id=user.id, name=user.name, email=user.email,
        role=user.role, role_id=user.role_id,
        assignments=[AssignmentOut.model_validate(a) for a in assignments],
    )


@router.post("/users/{user_id}/assign", response_model=AssignmentOut, status_code=201)
def add_assignment(
    user_id: int,
    data: AddAssignmentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.manage")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if db.query(Assignment).filter(
        Assignment.user_email == user.email,
        Assignment.project_code == data.project_code,
    ).first():
        raise HTTPException(status_code=400, detail="El usuario ya está asignado a ese proyecto")

    assignment = Assignment(
        user_email=user.email,
        project_code=data.project_code,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return AssignmentOut.model_validate(assignment)


@router.post("/users/{user_id}/impersonate", response_model=ImpersonateResponse)
def impersonate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.manage")),
):
    """Generate a short-lived token that lets an ADMIN view the app as another user."""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only ADMIN users can impersonate.")

    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot impersonate yourself.")
    if target.role == "ADMIN":
        raise HTTPException(status_code=400, detail="Cannot impersonate another ADMIN user.")

    # Short-lived token (60 min) with imp_by claim for audit
    token = create_access_token(
        data={"sub": str(target.id), "imp_by": str(current_user.id)},
        expires_delta=timedelta(minutes=60),
    )

    user_payload = build_user_response(target, db, imp_by_id=str(current_user.id))
    return ImpersonateResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(**user_payload),
    )


@router.delete("/users/{user_id}/assign/{assignment_id}", status_code=204)
def remove_assignment(
    user_id: int,
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.manage")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    assignment = db.get(Assignment, assignment_id)
    if not assignment or assignment.user_email != user.email:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    db.delete(assignment)
    db.commit()
    return None


# ── Assignments (CRUD directo) ────────────────────────────────────────────────

def _assignment_detail(a: Assignment, db: Session) -> AssignmentDetailOut:
    user = db.query(User).filter(User.email == a.user_email).first()
    return AssignmentDetailOut(
        id=a.id,
        user_id=user.id if user else 0,
        user_name=user.name if user else a.user_email,
        user_email=a.user_email,
        project_code=a.project_code,
        start_date=a.start_date,
        end_date=a.end_date,
    )


@router.get("/assignments", response_model=List[AssignmentDetailOut])
def list_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.manage")),
):
    """List all user-project assignments with user details."""
    assignments = (
        db.query(Assignment)
        .join(User, User.email == Assignment.user_email)
        .order_by(User.name, Assignment.project_code)
        .all()
    )
    return [_assignment_detail(a, db) for a in assignments]


@router.post("/assignments", response_model=AssignmentDetailOut, status_code=201)
def create_assignment_direct(
    data: CreateAssignmentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.manage")),
):
    """Create an assignment by user_id and project_code."""
    user = db.get(User, data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if db.query(Assignment).filter(
        Assignment.user_email == user.email,
        Assignment.project_code == data.project_code,
    ).first():
        raise HTTPException(status_code=400, detail="User is already assigned to this project")

    a = Assignment(
        user_email=user.email,
        project_code=data.project_code,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return _assignment_detail(a, db)


@router.put("/assignments/{assignment_id}", response_model=AssignmentDetailOut)
def update_assignment_direct(
    assignment_id: int,
    data: UpdateAssignmentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.manage")),
):
    a = db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if data.start_date is not None:
        a.start_date = data.start_date
    if data.end_date is not None:
        a.end_date = data.end_date
    elif "end_date" in data.model_fields_set:
        a.end_date = None   # allow clearing end date

    db.commit()
    db.refresh(a)
    return _assignment_detail(a, db)


@router.delete("/assignments/{assignment_id}", status_code=204)
def delete_assignment_direct(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.manage")),
):
    a = db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found")

    db.delete(a)
    db.commit()
    return None


# ── Permisos ──────────────────────────────────────────────────────────────────

@router.get("/permissions", response_model=List[PermissionOut])
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
):
    return db.query(Permission).order_by(Permission.code).all()


# ── Roles ─────────────────────────────────────────────────────────────────────

@router.get("/roles", response_model=List[RoleDetailOut])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
):
    roles = db.query(Role).order_by(Role.id).all()
    if not roles:
        return []

    role_ids = [r.id for r in roles]

    # Batch: all role→permission mappings in one query
    perm_rows = (
        db.query(RolePermission.role_id, Permission.code)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .filter(RolePermission.role_id.in_(role_ids))
        .all()
    )
    perms_by_role: dict[int, list[str]] = defaultdict(list)
    for role_id, code in perm_rows:
        perms_by_role[role_id].append(code)

    # Batch: user counts per role in one query
    count_rows = (
        db.query(User.role_id, func.count(User.id))
        .filter(User.role_id.in_(role_ids))
        .group_by(User.role_id)
        .all()
    )
    user_count_by_role = {role_id: count for role_id, count in count_rows}

    return [
        RoleDetailOut(
            role_id=r.id,
            role_name=r.name,
            description=r.description,
            permissions=perms_by_role[r.id],
            user_count=user_count_by_role.get(r.id, 0),
            is_system=r.is_system,
        )
        for r in roles
    ]


@router.post("/roles", response_model=RoleDetailOut, status_code=201)
def create_role(
    data: CreateRoleIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
):
    if db.query(Role).filter(Role.name == data.role_name).first():
        raise HTTPException(status_code=400, detail=f"El rol '{data.role_name}' ya existe")

    role = Role(name=data.role_name, description=data.description, is_system=False)
    db.add(role)
    db.commit()
    db.refresh(role)
    return _role_detail(role, db)


@router.put("/roles/{role_id}", response_model=RoleDetailOut)
def update_role(
    role_id: int,
    data: UpdateRoleIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
):
    role = _get_role_or_404(role_id, db)

    if data.description is not None:
        role.description = data.description

    if data.role_name is not None:
        if role.is_system:
            raise HTTPException(status_code=400, detail="No se puede renombrar un rol del sistema")
        if db.query(Role).filter(Role.name == data.role_name, Role.id != role_id).first():
            raise HTTPException(status_code=400, detail=f"El nombre '{data.role_name}' ya está en uso")
        # Users link via role_id FK — rename propagates automatically through relationship
        role.name = data.role_name

    db.commit()
    db.refresh(role)
    return _role_detail(role, db)


@router.delete("/roles/{role_id}", status_code=204)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
):
    role = _get_role_or_404(role_id, db)

    if role.is_system:
        raise HTTPException(status_code=400, detail="Los roles del sistema no pueden eliminarse")

    user_count = db.query(User).filter(User.role_id == role_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar: {user_count} usuario(s) tienen este rol asignado",
        )

    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    db.delete(role)
    db.commit()
    return None


@router.get("/roles/{role_id}/permissions", response_model=List[PermissionOut])
def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
):
    _get_role_or_404(role_id, db)
    return (
        db.query(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(RolePermission.role_id == role_id)
        .order_by(Permission.code)
        .all()
    )


@router.put("/roles/{role_id}/permissions", response_model=RoleDetailOut)
def set_role_permissions(
    role_id: int,
    data: SetRolePermissionsIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
):
    role = _get_role_or_404(role_id, db)

    # Resolver códigos a IDs
    valid_perms = {p.code: p.id for p in db.query(Permission).all()}
    for code in data.permissions:
        if code not in valid_perms:
            raise HTTPException(status_code=400, detail=f"Permiso desconocido: '{code}'")

    # Reemplazar permisos del rol
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    for code in data.permissions:
        db.add(RolePermission(role_id=role_id, permission_id=valid_perms[code]))
    db.commit()

    return _role_detail(role, db)
