"""Project management router — paginated, searchable, filterable."""
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional

from ..dependencies import get_db
from ..models import User, Project, UserLegalEntity
from ..schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectListResponse, ProjectPageResponse,
)
from ..auth.permissions import require_permission, get_user_project_ids

router = APIRouter(prefix="/projects", tags=["projects"])

_SORT_COLS = {
    "project_code": Project.project_code,
    "project_name": Project.project_name,
    "client_name":  Project.client_name,
    "status":       Project.status,
}


def _get_user_legal_entity_ids(user: User, db: Session) -> List[int]:
    """Get legal entity IDs for non-admin users based on UserLegalEntity associations."""
    if user.role == "ADMIN":
        return []  # Empty list signals "no filter"

    return [
        r.legal_entity_id for r in (
            db.query(UserLegalEntity.legal_entity_id)
            .filter(UserLegalEntity.user_id == user.id)
            .distinct()
            .all()
        )
    ]


def _base_query(current_user: User, db: Session):
    """Return a scoped base query with RBAC filtering.

    - ADMIN: all projects
    - Non-ADMIN: projects where legal_entity_id is in user's UserLegalEntity associations
    """
    q = db.query(Project)

    if current_user.role != "ADMIN":
        le_ids = _get_user_legal_entity_ids(current_user, db)
        if not le_ids:
            return None  # User has no legal entities → empty result

        q = q.filter(Project.legal_entity_id.in_(le_ids))

    return q


@router.get("/", response_model=ProjectPageResponse)
def list_projects(
    page:      int            = Query(1,  ge=1),
    page_size: int            = Query(25, ge=1, le=200),
    search:    str            = Query("", max_length=100),
    status:    Optional[str]  = Query(None),
    sort_by:   str            = Query("project_code"),
    sort_dir:  str            = Query("asc"),
    db:        Session        = Depends(get_db),
    current_user: User        = Depends(require_permission("project.view")),
):
    """Paginated project list with optional search, status filter and sort."""
    q = _base_query(current_user, db)
    if q is None:
        return ProjectPageResponse(items=[], total=0, page=page, page_size=page_size, pages=0)

    if search.strip():
        term = f"%{search.strip()}%"
        q = q.filter(
            or_(
                Project.project_code.ilike(term),
                Project.project_name.ilike(term),
                Project.client_name.ilike(term),
            )
        )

    if status:
        q = q.filter(Project.status == status)

    col = _SORT_COLS.get(sort_by, Project.project_code)
    q = q.order_by(col.desc() if sort_dir == "desc" else col.asc())

    total = q.count()
    pages = math.ceil(total / page_size) if total else 0
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    return ProjectPageResponse(
        items=items, total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/all", response_model=ProjectPageResponse)
def list_all_projects(
    page:      int            = Query(1,  ge=1),
    page_size: int            = Query(25, ge=1, le=200),
    search:    str            = Query("", max_length=100),
    status:    Optional[str]  = Query(None),
    sort_by:   str            = Query("project_code"),
    sort_dir:  str            = Query("asc"),
    db:        Session        = Depends(get_db),
    current_user: User        = Depends(require_permission("project.view")),
):
    """Alias of GET / — same paginated response."""
    return list_projects(page, page_size, search, status, sort_by, sort_dir, db, current_user)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("project.view")),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.role != "ADMIN":
        allowed_ids = get_user_project_ids(current_user, db)
        if project.id not in allowed_ids:
            raise HTTPException(status_code=403, detail="Access to this project is not permitted.")

    return project


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("project.edit")),
):
    project = Project(**project_data.model_dump(), manager_id=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("project.edit")),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in project_data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project
