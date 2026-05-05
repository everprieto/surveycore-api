"""Survey configuration router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..dependencies import get_db
from ..models import (
    User, Survey, SurveyQuestion, SurveyRecipient, SurveyAccess,
    MasterQuestion, QuestionTranslation, QuestionOption, OptionTranslation,
    SurveyAnswer, SurveyResponse as SurveyResponseModel,
)
from ..schemas.survey import (
    SurveyCreate, SurveyUpdate, SurveyResponse,
    SurveyQuestionAdd, SurveyQuestionUpdate, SurveyQuestionResponse,
    RecipientCreate, RecipientResponse,
    AccessLinkResponse, SurveyConfigResponse,
    SendEmailRequest, SendEmailResponse,
)
from ..schemas.response import SurveyTakeResponse, QuestionForSurvey
from ..auth.permissions import require_permission, get_user_project_ids
from ..utils import generate_access_token

router = APIRouter(prefix="/surveys", tags=["surveys"])


def _check_survey_scope(survey: Survey, current_user: User, db: Session) -> None:
    """Raise 403 if non-ADMIN user doesn't have access to the survey's project."""
    if current_user.role == "ADMIN":
        return
    allowed_ids = get_user_project_ids(current_user, db)
    if survey.project_id not in allowed_ids:
        raise HTTPException(status_code=403, detail="Access to this survey is not permitted.")


@router.post("/", response_model=SurveyResponse, status_code=status.HTTP_201_CREATED)
def create_survey(
    survey_data: SurveyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.create")),
):
    if current_user.role != "ADMIN":
        allowed_ids = get_user_project_ids(current_user, db)
        if survey_data.project_id not in allowed_ids:
            raise HTTPException(status_code=403, detail="You are not assigned to this project.")

    survey = Survey(
        project_id=survey_data.project_id,
        survey_type=survey_data.survey_type,
        language_code=survey_data.language_code,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        planned_send_date=survey_data.planned_send_date,
        survey_status="DRAFT",
    )
    db.add(survey)
    db.commit()
    db.refresh(survey)
    return survey


@router.get("/{survey_id}", response_model=SurveyConfigResponse)
def get_survey_config(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("project.view")),
):
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    _check_survey_scope(survey, current_user, db)

    survey_questions = (
        db.query(SurveyQuestion).filter_by(survey_id=survey_id)
        .order_by(SurveyQuestion.display_order).all()
    )
    recipients = db.query(SurveyRecipient).filter_by(survey_id=survey_id).all()
    access_links = db.query(SurveyAccess).filter_by(survey_id=survey_id).all()

    return {"survey": survey, "questions": survey_questions, "recipients": recipients, "access_links": access_links}


@router.put("/{survey_id}", response_model=SurveyResponse)
def update_survey(
    survey_id: int,
    survey_data: SurveyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.edit")),
):
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    _check_survey_scope(survey, current_user, db)

    if survey_data.survey_type:
        survey.survey_type = survey_data.survey_type
    if survey_data.language_code:
        survey.language_code = survey_data.language_code
    if survey_data.planned_send_date:
        survey.planned_send_date = survey_data.planned_send_date
    if survey_data.survey_status:
        survey.survey_status = survey_data.survey_status

    db.commit()
    db.refresh(survey)
    return survey


@router.post("/{survey_id}/questions", response_model=SurveyQuestionResponse, status_code=status.HTTP_201_CREATED)
def add_question_to_survey(
    survey_id: int,
    question_data: SurveyQuestionAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.edit")),
):
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    _check_survey_scope(survey, current_user, db)

    question = db.get(MasterQuestion, question_data.master_question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.status != "PUBLISHED":
        raise HTTPException(status_code=400, detail="Only published questions can be added to surveys")

    count = db.query(SurveyQuestion).filter_by(survey_id=survey_id).count()
    sq = SurveyQuestion(
        survey_id=survey_id,
        master_question_id=question_data.master_question_id,
        display_order=count + 1,
    )
    db.add(sq)
    db.commit()
    db.refresh(sq)
    return sq


@router.delete("/{survey_id}/questions/{sq_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_question_from_survey(
    survey_id: int,
    sq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.edit")),
):
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    _check_survey_scope(survey, current_user, db)

    sq = db.get(SurveyQuestion, sq_id)
    if not sq or sq.survey_id != survey_id:
        raise HTTPException(status_code=404, detail="Survey question not found")

    # Delete dependent SurveyAnswer records before deleting the question
    db.query(SurveyAnswer).filter_by(question_id=sq_id).delete(synchronize_session=False)
    db.delete(sq)
    db.commit()


@router.patch("/{survey_id}/questions/{sq_id}", response_model=SurveyQuestionResponse)
def update_question_in_survey(
    survey_id: int,
    sq_id: int,
    question_data: SurveyQuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.edit")),
):
    sq = db.get(SurveyQuestion, sq_id)
    if not sq or sq.survey_id != survey_id:
        raise HTTPException(status_code=404, detail="Survey question not found")

    survey = db.get(Survey, survey_id)
    _check_survey_scope(survey, current_user, db)

    if question_data.is_required is not None:
        sq.is_required = question_data.is_required

    db.commit()
    db.refresh(sq)
    return sq


@router.post("/{survey_id}/recipients", response_model=RecipientResponse, status_code=status.HTTP_201_CREATED)
def add_recipient(
    survey_id: int,
    recipient_data: RecipientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.edit")),
):
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    _check_survey_scope(survey, current_user, db)

    recipient = SurveyRecipient(
        survey_id=survey_id,
        recipient_name=recipient_data.recipient_name,
        recipient_email=recipient_data.recipient_email,
        company=recipient_data.company,
        role=recipient_data.role,
    )
    db.add(recipient)
    db.commit()
    db.refresh(recipient)
    return recipient


@router.delete("/{survey_id}/recipients/{recipient_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_recipient(
    survey_id: int,
    recipient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.edit")),
):
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    _check_survey_scope(survey, current_user, db)

    recipient = db.get(SurveyRecipient, recipient_id)
    if not recipient or recipient.survey_id != survey_id:
        raise HTTPException(status_code=404, detail="Recipient not found")

    # Cascade delete: responses -> answers -> access -> recipient
    survey_accesses = db.query(SurveyAccess).filter_by(recipient_id=recipient_id).all()
    for access in survey_accesses:
        responses = db.query(SurveyResponseModel).filter_by(survey_access_id=access.id).all()
        for response in responses:
            db.query(SurveyAnswer).filter_by(response_id=response.id).delete(synchronize_session=False)
        db.query(SurveyResponseModel).filter_by(survey_access_id=access.id).delete(synchronize_session=False)

    db.query(SurveyAccess).filter_by(recipient_id=recipient_id).delete(synchronize_session=False)
    db.delete(recipient)
    db.commit()


@router.post("/{survey_id}/generate-links", response_model=List[AccessLinkResponse])
def generate_access_links(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.send")),
):
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    _check_survey_scope(survey, current_user, db)

    recipients = db.query(SurveyRecipient).filter_by(survey_id=survey_id).all()
    for recipient in recipients:
        exists = db.query(SurveyAccess).filter_by(survey_id=survey_id, recipient_id=recipient.id).first()
        if not exists:
            db.add(SurveyAccess(
                survey_id=survey_id,
                recipient_id=recipient.id,
                access_token=generate_access_token(),
                status="PENDING",
                created_at=datetime.utcnow(),
            ))
    db.commit()
    return db.query(SurveyAccess).filter_by(survey_id=survey_id).all()


@router.post("/{survey_id}/send-emails", response_model=SendEmailResponse)
def send_survey_emails_endpoint(
    survey_id: int,
    request: SendEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.send")),
):
    """Send survey access links to recipients via email."""
    from ..services.email_service import send_survey_emails

    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    _check_survey_scope(survey, current_user, db)

    # Get access links for the survey (excluding COMPLETED)
    query = db.query(SurveyAccess).filter_by(survey_id=survey_id)
    if request.recipient_ids:
        query = query.filter(SurveyAccess.recipient_id.in_(request.recipient_ids))
    query = query.filter(SurveyAccess.status != "COMPLETED")
    access_links = query.all()

    if not access_links:
        raise HTTPException(status_code=400, detail="No access links found to send")

    # Build email data with recipient info
    email_data = []
    for access in access_links:
        recipient = db.get(SurveyRecipient, access.recipient_id)
        if recipient:
            email_data.append({
                "recipient_name": recipient.recipient_name,
                "recipient_email": recipient.recipient_email,
                "access_token": access.access_token,
            })

    # Send emails via Azure Communication Services
    result = send_survey_emails(
        access_links=email_data,
        survey_name=survey.survey_type,
        survey_type=survey.survey_type,
    )

    # Update status to SENT if any succeeded
    if result["success_count"] > 0:
        for access in access_links:
            access.status = "SENT"
        survey.survey_status = "SENT"
        db.commit()
        db.refresh(survey)

    return result


@router.get("/{survey_id}/preview", response_model=SurveyTakeResponse)
def preview_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("project.view")),
):
    """Return survey questions with translations for authenticated preview.
    Identical logic to the public take-survey endpoint but requires auth + project scope."""
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    _check_survey_scope(survey, current_user, db)

    survey_questions = (
        db.query(SurveyQuestion)
        .filter_by(survey_id=survey_id)
        .order_by(SurveyQuestion.display_order)
        .all()
    )

    enriched: list[QuestionForSurvey] = []
    for sq in survey_questions:
        master = db.get(MasterQuestion, sq.master_question_id)
        if not master:
            continue

        translation = (
            db.query(QuestionTranslation)
            .filter_by(master_question_id=master.id, language_code=survey.language_code)
            .first()
        ) or (
            db.query(QuestionTranslation)
            .filter_by(master_question_id=master.id, is_default_language=True)
            .first()
        )
        question_text = translation.question_text if translation else master.logical_code

        options = []
        if master.answer_type in ["DROPDOWN", "MULTI_SELECT"]:
            for opt in db.query(QuestionOption).filter_by(master_question_id=master.id).all():
                opt_t = db.query(OptionTranslation).filter_by(
                    option_id=opt.id, language_code=survey.language_code
                ).first()
                options.append({"id": opt.id, "text": opt_t.option_text if opt_t else opt.option_text})

        enriched.append(QuestionForSurvey(
            sq_id=sq.id,
            answer_type=master.answer_type,
            question_text=question_text,
            options=options,
            is_required=sq.is_required,
        ))

    return SurveyTakeResponse(
        survey_id=survey.id,
        survey_type=survey.survey_type,
        language_code=survey.language_code,
        access_status="PREVIEW",
        questions=enriched,
    )
