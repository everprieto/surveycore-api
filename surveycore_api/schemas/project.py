"""Project schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProjectCreate(BaseModel):
    """Create new project."""
    project_code: str
    project_name: str
    client_name: str
    cost_center: str
    client_manager_email: Optional[str] = None
    delivery_manager_email: Optional[str] = None
    client_exec_mgr_act_email: Optional[str] = None
    delivery_exec_mgr_act_email: Optional[str] = None
    project_head_email: Optional[str] = None
    legal_entity_name: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str = "ACTIVE"


class ProjectUpdate(BaseModel):
    """Update existing project."""
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    cost_center: Optional[str] = None
    client_manager_email: Optional[str] = None
    delivery_manager_email: Optional[str] = None
    client_exec_mgr_act_email: Optional[str] = None
    delivery_exec_mgr_act_email: Optional[str] = None
    project_head_email: Optional[str] = None
    legal_entity_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    """Project response."""
    id: int
    project_code: str
    project_name: str
    client_name: str
    cost_center: str
    client_manager_email: Optional[str]
    delivery_manager_email: Optional[str]
    client_exec_mgr_act_email: Optional[str]
    delivery_exec_mgr_act_email: Optional[str]
    project_head_email: Optional[str]
    legal_entity_name: Optional[str]
    manager_id: int
    start_date: datetime
    end_date: Optional[datetime]
    status: str

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Simplified project list item."""
    id: int
    project_code: str
    project_name: str
    client_name: str
    cost_center: str
    client_manager_email: Optional[str]
    delivery_manager_email: Optional[str]
    client_exec_mgr_act_email: Optional[str]
    delivery_exec_mgr_act_email: Optional[str]
    project_head_email: Optional[str]
    legal_entity_name: Optional[str]
    status: str

    class Config:
        from_attributes = True


class ProjectPageResponse(BaseModel):
    """Paginated project list."""
    items: List[ProjectListResponse]
    total: int
    page: int
    page_size: int
    pages: int
