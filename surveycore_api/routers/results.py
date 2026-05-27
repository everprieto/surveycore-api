"""Survey results and dashboard router."""
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from typing import List, Optional

from ..dependencies import get_db
from ..models import (
    User, Survey, Project, SurveyType, SurveyQuestion, MasterQuestion,
    SurveyAccess, SurveyResponse, SurveyAnswer, SurveyRecipient,
    UserLegalEntity
)
from ..schemas.response import (
    SurveyResults, QuestionResult, AnswerResult,
    CompletionStats, ControlTowerRow, ControlTowerPage, ControlTowerTotals
)
from ..auth.permissions import require_permission, get_user_project_ids

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/survey/{survey_id}", response_model=SurveyResults)
def get_survey_results(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("results.view")),
):
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    if current_user.role != "ADMIN":
        allowed_ids = get_user_project_ids(current_user, db)
        if survey.project_id not in allowed_ids:
            raise HTTPException(status_code=403, detail="Access to this survey is not permitted.")

    total_sent = db.query(SurveyAccess).filter_by(survey_id=survey_id).count()
    total_completed = db.query(SurveyAccess).filter_by(survey_id=survey_id, status="COMPLETED").count()

    survey_questions = (
        db.query(SurveyQuestion)
        .filter_by(survey_id=survey_id)
        .order_by(SurveyQuestion.display_order)
        .all()
    )

    question_results = []
    for sq in survey_questions:
        master = db.get(MasterQuestion, sq.master_question_id)
        if not master:
            continue

        answers = db.query(SurveyAnswer).filter_by(question_id=sq.id).all()
        answer_rows = []
        for answer in answers:
            response = db.get(SurveyResponse, answer.response_id)
            if not response:
                continue
            access = db.get(SurveyAccess, response.survey_access_id)
            if not access:
                continue
            recipient = db.get(SurveyRecipient, access.recipient_id)
            answer_rows.append(AnswerResult(
                respondent=recipient.recipient_name if recipient else "Unknown",
                company=recipient.company if recipient else "",
                answer=answer.comment,
                score=answer.score,
                answer_type=master.answer_type,
            ))

        question_results.append(QuestionResult(
            sq_id=sq.id,
            logical_code=master.logical_code,
            question_text=master.logical_code,
            answer_type=master.answer_type,
            answers=answer_rows,
            response_count=len(answer_rows),
        ))

    return SurveyResults(
        survey_id=survey.id,
        survey_type=survey.type_obj.survey_type if survey.type_obj else "Unknown",
        language_code=survey.language_code,
        total_sent=total_sent,
        total_completed=total_completed,
        questions=question_results,
    )


@router.get("/user/surveys", response_model=List[CompletionStats])
def get_user_surveys_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("survey.create")),
):
    """Get all surveys created by the current user."""
    surveys = db.query(Survey).filter_by(created_by=current_user.id).all()
    stats_list = []
    for survey in surveys:
        total_sent = db.query(SurveyAccess).filter_by(survey_id=survey.id).count()
        total_completed = db.query(SurveyAccess).filter_by(survey_id=survey.id, status="COMPLETED").count()
        last_response = (
            db.query(SurveyResponse)
            .join(SurveyAccess)
            .filter(SurveyAccess.survey_id == survey.id)
            .order_by(SurveyResponse.submitted_at.desc())
            .first()
        )
        project = db.get(Project, survey.project_id) if survey.project_id else None
        stats_list.append(CompletionStats(
            survey_id=survey.id,
            survey_type=survey.type_obj.survey_type if survey.type_obj else "Unknown",
            language_code=survey.language_code,
            planned_send_date=str(survey.planned_send_date) if survey.planned_send_date else None,
            survey_status=survey.survey_status,
            total_sent=total_sent,
            total_completed=total_completed,
            last_response_at=last_response.submitted_at if last_response else None,
            project_name=project.project_name if project else None,
        ))
    return stats_list


@router.get("/project/{project_id}/surveys", response_model=List[CompletionStats])
def get_project_surveys_stats(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("results.view")),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.role != "ADMIN":
        allowed_ids = get_user_project_ids(current_user, db)
        if project_id not in allowed_ids:
            raise HTTPException(status_code=403, detail="Access to this project is not permitted.")

    surveys = db.query(Survey).filter_by(project_id=project_id).all()
    stats_list = []
    for survey in surveys:
        total_sent = db.query(SurveyAccess).filter_by(survey_id=survey.id).count()
        total_completed = db.query(SurveyAccess).filter_by(survey_id=survey.id, status="COMPLETED").count()
        last_response = (
            db.query(SurveyResponse)
            .join(SurveyAccess)
            .filter(SurveyAccess.survey_id == survey.id)
            .order_by(SurveyResponse.submitted_at.desc())
            .first()
        )
        stats_list.append(CompletionStats(
            survey_id=survey.id,
            survey_type=survey.type_obj.survey_type if survey.type_obj else "Unknown",
            language_code=survey.language_code,
            planned_send_date=str(survey.planned_send_date),
            survey_status=survey.survey_status,
            total_sent=total_sent,
            total_completed=total_completed,
            last_response_at=last_response.submitted_at if last_response else None,
        ))
    return stats_list


@router.get("/control-tower", response_model=ControlTowerPage)
def get_control_tower(
    page:          int           = Query(1,   ge=1),
    page_size:     int           = Query(25,  ge=1, le=200),
    search:        str           = Query("",  max_length=100),
    survey_status: Optional[str] = Query(None),
    language_code: Optional[str] = Query(None),
    sort_by:       str           = Query("project_code"),
    sort_dir:      str           = Query("asc"),
    db:            Session       = Depends(get_db),
    current_user:  User          = Depends(require_permission("results.view")),
):
    """Paginated Control Tower — single JOIN query, no N+1."""

    # ── Subqueries for counts ──────────────────────────────────────────────────
    sent_sq = (
        db.query(SurveyAccess.survey_id,
                 func.count(SurveyAccess.id).label("sent_count"))
        .group_by(SurveyAccess.survey_id).subquery()
    )
    done_sq = (
        db.query(SurveyAccess.survey_id,
                 func.count(SurveyAccess.id).label("done_count"))
        .filter(SurveyAccess.status == "COMPLETED")
        .group_by(SurveyAccess.survey_id).subquery()
    )
    last_sq = (
        db.query(SurveyAccess.survey_id,
                 func.max(SurveyResponse.submitted_at).label("last_response"))
        .join(SurveyResponse, SurveyResponse.survey_access_id == SurveyAccess.id)
        .group_by(SurveyAccess.survey_id).subquery()
    )

    # ── Base query (with optional project join) ─────────────────────────────────
    q = (
        db.query(
            Survey.id.label("survey_id"),
            SurveyType.survey_type,
            Survey.language_code,
            Survey.survey_status,
            Survey.planned_send_date,
            Project.project_code,
            Project.project_name,
            User.name.label("manager_name"),
            func.coalesce(sent_sq.c.sent_count, 0).label("sent_count"),
            func.coalesce(done_sq.c.done_count, 0).label("done_count"),
            last_sq.c.last_response,
        )
        .outerjoin(Project, Survey.project_id == Project.id)
        .outerjoin(SurveyType, Survey.survey_type_id == SurveyType.id)
        .outerjoin(User, Project.manager_id == User.id)
        .outerjoin(sent_sq, sent_sq.c.survey_id == Survey.id)
        .outerjoin(done_sq, done_sq.c.survey_id == Survey.id)
        .outerjoin(last_sq, last_sq.c.survey_id == Survey.id)
    )

    # ── Scope filter: only surveys user can see ──────────────────────────────────
    if current_user.role != "ADMIN":
        # Get legal entity IDs for non-admin users
        le_ids = [
            r.legal_entity_id for r in (
                db.query(UserLegalEntity.legal_entity_id)
                .filter(UserLegalEntity.user_id == current_user.id)
                .distinct()
                .all()
            )
        ]
        # Show surveys that:
        # 1) User created (created_by = current_user.id) OR
        # 2) Are in projects where user has legal entity access
        q = q.filter(
            or_(
                Survey.created_by == current_user.id,
                Project.legal_entity_id.in_(le_ids) if le_ids else False
            )
        )

    # ── Global totals (scoped, before search/pagination) ──────────────────────
    totals_r = q.with_entities(
        func.count(Survey.id),
        func.count(func.distinct(Project.id)),
        func.coalesce(func.sum(func.coalesce(sent_sq.c.sent_count, 0)), 0),
        func.coalesce(func.sum(func.coalesce(done_sq.c.done_count, 0)), 0),
    ).one()
    totals = ControlTowerTotals(
        total_surveys=totals_r[0],
        total_projects=totals_r[1],
        total_sent=int(totals_r[2]),
        total_completed=int(totals_r[3]),
    )

    # ── Search ─────────────────────────────────────────────────────────────────
    if search.strip():
        term = f"%{search.strip()}%"
        q = q.filter(or_(
            Project.project_code.ilike(term),
            Project.project_name.ilike(term),
            SurveyType.survey_type.ilike(term),
        ))

    # ── Filters ────────────────────────────────────────────────────────────────
    if survey_status:
        q = q.filter(Survey.survey_status == survey_status)
    if language_code:
        q = q.filter(Survey.language_code == language_code)

    # ── Sorting ────────────────────────────────────────────────────────────────
    _SORT = {
        "project_code":  Project.project_code,
        "project_name":  Project.project_name,
        "survey_type":   SurveyType.survey_type,
        "survey_status": Survey.survey_status,
        "sent_count":    sent_sq.c.sent_count,
        "done_count":    done_sq.c.done_count,
        "last_response": last_sq.c.last_response,
    }
    col = _SORT.get(sort_by, Survey.id)
    q = q.order_by(col.desc() if sort_dir == "desc" else col.asc())

    # ── Pagination ─────────────────────────────────────────────────────────────
    total = q.count()
    pages = math.ceil(total / page_size) if total else 0
    rows  = q.offset((page - 1) * page_size).limit(page_size).all()

    return ControlTowerPage(
        items=[
            ControlTowerRow(
                survey_id=r.survey_id,
                project_code=r.project_code,
                project_name=r.project_name,
                manager_name=r.manager_name or "N/A",
                survey_type=r.survey_type,
                language_code=r.language_code,
                sent_count=r.sent_count,
                done_count=r.done_count,
                last_response=r.last_response,
                survey_status=r.survey_status,
                planned_send_date=r.planned_send_date,
            )
            for r in rows
        ],
        total=total, page=page, page_size=page_size, pages=pages, totals=totals,
    )
