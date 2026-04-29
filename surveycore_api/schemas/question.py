"""Question library schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class QuestionOptionBase(BaseModel):
    """Base question option schema."""
    option_text: str


class QuestionOptionCreate(QuestionOptionBase):
    """Create question option."""
    pass


class QuestionOptionResponse(QuestionOptionBase):
    """Question option response."""
    id: int
    master_question_id: int

    class Config:
        from_attributes = True


class OptionTranslationCreate(BaseModel):
    """Create option translation."""
    option_id: int
    language_code: str
    option_text: str


class OptionTranslationResponse(BaseModel):
    """Option translation response."""
    id: int
    option_id: int
    language_code: str
    option_text: str

    class Config:
        from_attributes = True


class QuestionTranslationCreate(BaseModel):
    """Create question translation."""
    language_code: str
    question_text: str
    is_default_language: bool = False


class QuestionTranslationResponse(BaseModel):
    """Question translation response."""
    id: int
    master_question_id: int
    language_code: str
    question_text: str
    is_default_language: bool

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    """Create new question."""
    logical_code: str
    answer_type: str  # RATING, DROPDOWN, MULTI_SELECT, TEXT, YES_NO
    question_text: str  # Default translation (EN)
    options: Optional[List[str]] = None  # For DROPDOWN/MULTI_SELECT


class QuestionUpdate(BaseModel):
    """Update existing question (only DRAFT)."""
    logical_code: Optional[str] = None
    answer_type: Optional[str] = None
    question_text: Optional[str] = None
    options: Optional[List[str]] = None


class QuestionResponse(BaseModel):
    """Question response with translations."""
    id: int
    logical_code: str
    status: str
    answer_type: str
    created_by: int
    created_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    translations: List[QuestionTranslationResponse]
    options: List[QuestionOptionResponse]

    class Config:
        from_attributes = True


class QuestionListResponse(BaseModel):
    """Simplified question list item."""
    id: int
    logical_code: str
    status: str
    answer_type: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
