"""Public routes for survey taking (no authentication)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from ..dependencies import get_db
from ..models import (
    SurveyAccess, Survey, SurveyQuestion, MasterQuestion,
    QuestionTranslation, QuestionOption, OptionTranslation,
    SurveyResponse, SurveyAnswer
)
from ..schemas.response import SurveyTakeResponse, SurveySubmit, QuestionForSurvey

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/survey/{token}", response_model=SurveyTakeResponse)
def get_survey_by_token(token: str, db: Session = Depends(get_db)):
    """Get survey data for taking (public access via token)."""
    # Find access token
    access = db.query(SurveyAccess).filter_by(access_token=token).first()
    if not access:
        raise HTTPException(status_code=404, detail="Invalid survey link")

    # Check if already completed
    if access.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Survey already completed")

    # Update status to OPENED if PENDING or SENT
    if access.status in ["PENDING", "SENT"]:
        access.status = "OPENED"
        access.opened_at = datetime.utcnow()
        db.commit()

    # Get survey
    survey = db.get(Survey, access.survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    # Get questions in order
    survey_questions = db.query(SurveyQuestion).filter_by(
        survey_id=survey.id
    ).order_by(SurveyQuestion.display_order).all()

    # Enrich questions with translations and options
    enriched_questions = []
    for sq in survey_questions:
        master = db.get(MasterQuestion, sq.master_question_id)
        if not master:
            continue

        # Get translation in survey language
        translation = db.query(QuestionTranslation).filter_by(
            master_question_id=master.id,
            language_code=survey.language_code
        ).first()

        # Fallback to default language
        if not translation:
            translation = db.query(QuestionTranslation).filter_by(
                master_question_id=master.id,
                is_default_language=True
            ).first()

        question_text = translation.question_text if translation else master.logical_code

        # Get options if applicable
        options = []
        if master.answer_type in ["DROPDOWN", "MULTI_SELECT"]:
            master_options = db.query(QuestionOption).filter_by(
                master_question_id=master.id
            ).all()

            for opt in master_options:
                opt_translation = db.query(OptionTranslation).filter_by(
                    option_id=opt.id,
                    language_code=survey.language_code
                ).first()

                option_text = opt_translation.option_text if opt_translation else opt.option_text
                options.append({"id": opt.id, "text": option_text})

        enriched_questions.append(QuestionForSurvey(
            sq_id=sq.id,
            answer_type=master.answer_type,
            question_text=question_text,
            options=options,
            is_required=sq.is_required,
        ))

    return SurveyTakeResponse(
        survey_id=survey.id,
        survey_type=survey.type_obj.survey_type if survey.type_obj else "Unknown",
        language_code=survey.language_code,
        access_status=access.status,
        questions=enriched_questions
    )


@router.post("/survey/{token}/submit")
def submit_survey(token: str, submission: SurveySubmit, db: Session = Depends(get_db)):
    """Submit survey responses (public access via token)."""
    # Find access token
    access = db.query(SurveyAccess).filter_by(access_token=token).first()
    if not access:
        raise HTTPException(status_code=404, detail="Invalid survey link")

    # Check if already completed
    if access.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Survey already completed")

    # Create response record
    response = SurveyResponse(
        survey_access_id=access.id,
        submitted_at=datetime.utcnow()
    )
    db.add(response)
    db.commit()
    db.refresh(response)

    # Save answers
    for answer_data in submission.answers:
        sq = db.get(SurveyQuestion, answer_data.sq_id)
        if not sq:
            continue

        answer = SurveyAnswer(
            response_id=response.id,
            question_id=sq.id,
            score=answer_data.score,
            comment=answer_data.answer_value
        )
        db.add(answer)

    # Update access status
    access.status = "COMPLETED"
    access.completed_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Survey submitted successfully",
        "response_id": response.id,
        "submitted_at": response.submitted_at
    }
