"""Survey response and results schemas."""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class QuestionForSurvey(BaseModel):
    """Question formatted for survey taking."""
    sq_id: int
    answer_type: str
    question_text: str
    options: List[dict]  # [{id: int, text: str}]


class SurveyTakeResponse(BaseModel):
    """Data for taking a survey."""
    survey_id: int
    survey_type: str
    language_code: str
    access_status: str
    questions: List[QuestionForSurvey]


class AnswerSubmit(BaseModel):
    """Single answer submission."""
    sq_id: int
    answer_value: Optional[str] = None  # Text, dropdown, or comma-separated multi-select
    score: Optional[int] = None  # For RATING type


class SurveySubmit(BaseModel):
    """Complete survey submission."""
    answers: List[AnswerSubmit]


class AnswerResult(BaseModel):
    """Single answer result."""
    respondent: str
    company: str
    answer: Optional[str]
    score: Optional[int]
    answer_type: str


class QuestionResult(BaseModel):
    """Results for a single question."""
    sq_id: int
    logical_code: str
    question_text: str
    answer_type: str
    answers: List[AnswerResult]
    response_count: int


class SurveyResults(BaseModel):
    """Complete survey results."""
    survey_id: int
    survey_type: str
    language_code: str
    total_sent: int
    total_completed: int
    questions: List[QuestionResult]


class CompletionStats(BaseModel):
    """Survey completion statistics."""
    survey_id: int
    survey_type: str
    language_code: str
    planned_send_date: str
    survey_status: str
    total_sent: int
    total_completed: int
    last_response_at: Optional[datetime]


class ControlTowerRow(BaseModel):
    """Single row in control tower dashboard."""
    survey_id: int
    project_code: str
    project_name: str
    manager_name: str
    survey_type: str
    language_code: str
    sent_count: int
    done_count: int
    last_response: Optional[datetime]
    survey_status: str
    planned_send_date: Optional[datetime] = None


class ControlTowerTotals(BaseModel):
    total_surveys: int
    total_projects: int
    total_sent: int
    total_completed: int


class ControlTowerPage(BaseModel):
    items: List[ControlTowerRow]
    total: int
    page: int
    page_size: int
    pages: int
    totals: ControlTowerTotals
