"""Question library router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime

from ..dependencies import get_db
from ..models import User, MasterQuestion, QuestionTranslation, QuestionOption, OptionTranslation
from ..schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionListResponse,
    QuestionTranslationCreate, QuestionTranslationResponse,
    OptionTranslationCreate, OptionTranslationResponse,
)
from ..auth.permissions import require_permission

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("/", response_model=List[QuestionListResponse])
def list_questions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("project.view")),
):
    return db.query(MasterQuestion).all()


@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("project.view")),
):
    question = db.query(MasterQuestion).options(
        joinedload(MasterQuestion.translations),
        joinedload(MasterQuestion.options),
        joinedload(MasterQuestion.survey_type)
    ).filter_by(id=question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.edit")),
):
    question = MasterQuestion(
        survey_type_id=question_data.survey_type_id,
        logical_code=question_data.logical_code,
        answer_type=question_data.answer_type,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        status="DRAFT",
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    db.add(QuestionTranslation(
        master_question_id=question.id,
        language_code="EN",
        question_text=question_data.question_text,
        is_default_language=True,
    ))

    if question_data.answer_type in ["DROPDOWN", "MULTI_SELECT"] and question_data.options:
        for opt in question_data.options:
            db.add(QuestionOption(master_question_id=question.id, option_text=opt.strip()))

    db.commit()

    # Reload question with all relationships
    question = db.query(MasterQuestion).options(
        joinedload(MasterQuestion.translations),
        joinedload(MasterQuestion.options),
        joinedload(MasterQuestion.survey_type)
    ).filter_by(id=question.id).first()
    return question


@router.put("/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: int,
    question_data: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.edit")),
):
    question = db.query(MasterQuestion).options(
        joinedload(MasterQuestion.translations),
        joinedload(MasterQuestion.options),
        joinedload(MasterQuestion.survey_type)
    ).filter_by(id=question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.status == "PUBLISHED":
        raise HTTPException(status_code=403, detail="Published questions cannot be edited")

    if question_data.survey_type_id:
        question.survey_type_id = question_data.survey_type_id
    if question_data.logical_code:
        question.logical_code = question_data.logical_code
    if question_data.answer_type:
        question.answer_type = question_data.answer_type

    if question_data.question_text:
        t = db.query(QuestionTranslation).filter_by(master_question_id=question_id, is_default_language=True).first()
        if t:
            t.question_text = question_data.question_text

    if question_data.options is not None and question_data.answer_type in ["DROPDOWN", "MULTI_SELECT"]:
        db.query(QuestionOption).filter_by(master_question_id=question_id).delete()
        for opt in question_data.options:
            db.add(QuestionOption(master_question_id=question_id, option_text=opt.strip()))

    db.commit()
    db.refresh(question, ["translations", "options", "survey_type"])
    return question


@router.post("/{question_id}/publish", response_model=QuestionResponse)
def publish_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.edit")),
):
    question = db.query(MasterQuestion).options(
        joinedload(MasterQuestion.translations),
        joinedload(MasterQuestion.options),
        joinedload(MasterQuestion.survey_type)
    ).filter_by(id=question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    question.status = "PUBLISHED"
    question.published_at = datetime.utcnow()
    db.commit()
    db.refresh(question, ["translations", "options", "survey_type"])
    return question


@router.post("/{question_id}/translations", response_model=QuestionTranslationResponse, status_code=status.HTTP_201_CREATED)
def add_translation(
    question_id: int,
    translation_data: QuestionTranslationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.edit")),
):
    if not db.get(MasterQuestion, question_id):
        raise HTTPException(status_code=404, detail="Question not found")
    t = QuestionTranslation(
        master_question_id=question_id,
        language_code=translation_data.language_code,
        question_text=translation_data.question_text,
        is_default_language=translation_data.is_default_language,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{question_id}/translations/{translation_id}", status_code=204)
def delete_translation(
    question_id: int,
    translation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.edit")),
):
    question = db.get(MasterQuestion, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.status == "PUBLISHED":
        raise HTTPException(status_code=403, detail="Published questions cannot be edited")

    translation = db.get(QuestionTranslation, translation_id)
    if not translation or translation.master_question_id != question_id:
        raise HTTPException(status_code=404, detail="Translation not found")
    if translation.is_default_language:
        raise HTTPException(status_code=400, detail="The default language translation cannot be deleted")

    db.delete(translation)
    db.commit()
    return None


@router.post("/options/translations", response_model=OptionTranslationResponse, status_code=status.HTTP_201_CREATED)
def add_option_translation(
    translation_data: OptionTranslationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.edit")),
):
    if not db.get(QuestionOption, translation_data.option_id):
        raise HTTPException(status_code=404, detail="Option not found")
    ot = OptionTranslation(
        option_id=translation_data.option_id,
        language_code=translation_data.language_code,
        option_text=translation_data.option_text,
    )
    db.add(ot)
    db.commit()
    db.refresh(ot)
    return ot
