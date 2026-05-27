"""Survey schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class SurveyTypeResponse(BaseModel):
    """Survey type response."""
    id: int
    survey_type: str

    class Config:
        from_attributes = True


class SurveyCreate(BaseModel):
    """Create new survey."""
    project_id: Optional[int] = None
    survey_type_id: int
    language_code: str
    planned_send_date: date


class SurveyUpdate(BaseModel):
    """Update survey."""
    survey_type_id: Optional[int] = None
    language_code: Optional[str] = None
    planned_send_date: Optional[datetime] = None
    survey_status: Optional[str] = None


class SurveyResponse(BaseModel):
    """Survey response."""
    id: int
    project_id: Optional[int] = None
    survey_type_id: int
    survey_type: Optional[str] = None  # Populate from type_obj.survey_type
    language_code: str
    created_by: int
    created_at: datetime
    planned_send_date: Optional[datetime] = None
    survey_status: str

    class Config:
        from_attributes = True

    def model_post_init(self, __context):
        """Extract survey_type from type_obj relationship."""
        if hasattr(self, 'type_obj') and self.type_obj:
            self.survey_type = self.type_obj.survey_type


class SurveyQuestionAdd(BaseModel):
    """Add question to survey."""
    master_question_id: int


class SurveyQuestionUpdate(BaseModel):
    """Update survey question."""
    is_required: Optional[bool] = None


class SurveyQuestionResponse(BaseModel):
    """Survey question response."""
    id: int
    survey_id: int
    master_question_id: int
    display_order: int
    is_required: bool = False

    class Config:
        from_attributes = True


class RecipientCreate(BaseModel):
    """Create survey recipient."""
    recipient_name: str
    recipient_email: str
    company: str
    role: str


class RecipientResponse(BaseModel):
    """Survey recipient response."""
    id: int
    survey_id: int
    recipient_name: str
    recipient_email: str
    company: str
    role: str

    class Config:
        from_attributes = True


class AccessLinkResponse(BaseModel):
    """Survey access link response."""
    id: int
    survey_id: int
    recipient_id: int
    access_token: str
    status: str
    created_at: datetime
    opened_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SurveyConfigResponse(BaseModel):
    """Complete survey configuration."""
    survey: SurveyResponse
    questions: List[SurveyQuestionResponse]
    recipients: List[RecipientResponse]
    access_links: List[AccessLinkResponse]


class SendEmailRequest(BaseModel):
    """Request to send survey emails."""
    recipient_ids: Optional[List[int]] = None  # None = send to all


class SendEmailResponse(BaseModel):
    """Email sending response."""
    success_count: int
    failed_count: int
    total: int
    errors: List[str]
