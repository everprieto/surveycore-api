from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)

    # Relationship — loaded eagerly to avoid N+1 on role name access
    role_obj = relationship("Role", foreign_keys=[role_id], lazy="joined")

    @property
    def role(self) -> str:
        """Role name derived from role_id FK — read-only."""
        return self.role_obj.name if self.role_obj else ""


class MasterQuestion(Base):
    __tablename__ = "master_questions"

    id = Column(Integer, primary_key=True)
    logical_code = Column(String)
    survey_type_id = Column(Integer, ForeignKey("survey_types.id"), nullable=False, index=True)
    status = Column(String)
    answer_type = Column(String)
    created_by = Column(Integer)
    created_at = Column(DateTime)
    published_at = Column(DateTime)

    translations = relationship("QuestionTranslation", back_populates="question")
    options = relationship("QuestionOption", backref="question")
    survey_type = relationship("SurveyType")


class QuestionTranslation(Base):
    __tablename__ = "question_translations"

    id = Column(Integer, primary_key=True)
    master_question_id = Column(Integer, ForeignKey("master_questions.id"))
    language_code = Column(String)
    question_text = Column(String)
    is_default_language = Column(Boolean)

    question = relationship("MasterQuestion", back_populates="translations")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    entity_type = Column(String)
    entity_id = Column(Integer)
    action = Column(String)
    performed_by = Column(Integer)

class QuestionOption(Base):

    __tablename__ = "question_options"

    id = Column(Integer, primary_key=True)

    master_question_id = Column(Integer, ForeignKey("master_questions.id"))

    option_text = Column(String)

class OptionTranslation(Base):

    __tablename__ = "option_translations"

    id = Column(Integer, primary_key=True)

    option_id = Column(Integer, ForeignKey("question_options.id"))

    language_code = Column(String)

    option_text = Column(String)



# -------------------------
# Project
# -------------------------

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)

    project_code = Column(String, unique=True, index=True, nullable=False)
    project_name = Column(String, index=True)

    client_name = Column(String, index=True)
    cost_center = Column(String)

    client_manager_email = Column(String, nullable=True)
    delivery_manager_email = Column(String, nullable=True)
    project_head_email = Column(String, nullable=True)
    legal_entity_id = Column(Integer, ForeignKey("legal_entities.id"), nullable=True, index=True)

    manager_id = Column(Integer, ForeignKey("users.id"), index=True)

    start_date = Column(DateTime)
    end_date = Column(DateTime)

    status = Column(String, index=True)

    surveys = relationship("Survey", backref="project")
    legal_entity = relationship("LegalEntity", foreign_keys=[legal_entity_id])


# -------------------------
# SurveyType
# -------------------------


class SurveyType(Base):
    __tablename__ = "survey_types"

    id = Column(Integer, primary_key=True)
    survey_type = Column(String, unique=True, nullable=False, index=True)

    surveys = relationship("Survey", back_populates="type_obj")


# -------------------------
# Survey
# -------------------------

class Survey(Base):
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True)

    project_id = Column(Integer, ForeignKey("projects.id"), index=True, nullable=True)

    survey_type_id = Column(Integer, ForeignKey("survey_types.id"), index=True)
    language_code = Column(String, index=True)

    created_by = Column(Integer, ForeignKey("users.id"))

    created_at = Column(DateTime, default=datetime.utcnow)

    planned_send_date = Column(DateTime)

    survey_status = Column(String, index=True)

    questions = relationship("SurveyQuestion", backref="survey")
    recipients = relationship("SurveyRecipient", backref="survey")
    type_obj = relationship("SurveyType", back_populates="surveys", lazy="joined")


# -------------------------
# SurveyQuestion
# -------------------------

class SurveyQuestion(Base):
    __tablename__ = "survey_questions"

    id = Column(Integer, primary_key=True)

    survey_id = Column(Integer, ForeignKey("surveys.id"))

    master_question_id = Column(Integer, ForeignKey("master_questions.id"))

    display_order = Column(Integer)

    is_required = Column(Boolean, default=True)


# -------------------------
# SurveyRecipient
# -------------------------

class SurveyRecipient(Base):
    __tablename__ = "survey_recipients"

    id = Column(Integer, primary_key=True)

    survey_id = Column(Integer, ForeignKey("surveys.id"))

    recipient_name = Column(String)
    recipient_email = Column(String)

    company = Column(String)

    role = Column(String)


# -------------------------
# SurveyAccess
# -------------------------

class SurveyAccess(Base):

    __tablename__ = "survey_access"

    id = Column(Integer, primary_key=True)

    survey_id = Column(Integer, ForeignKey("surveys.id"))
    recipient_id = Column(Integer, ForeignKey("survey_recipients.id"))

    access_token = Column(String, unique=True, index=True)

    status = Column(String, default="PENDING", index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    opened_at = Column(DateTime)
    completed_at = Column(DateTime)

    survey = relationship("Survey")
    recipient = relationship("SurveyRecipient")

# -------------------------
# SurveyResponse
# -------------------------
class SurveyResponse(Base):

    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True)

    survey_access_id = Column(Integer, ForeignKey("survey_access.id"))

    submitted_at = Column(DateTime)

    access = relationship("SurveyAccess")


# -------------------------
# SurveyAnswer
# -------------------------
class SurveyAnswer(Base):

    __tablename__ = "survey_answers"

    id = Column(Integer, primary_key=True)

    response_id = Column(Integer, ForeignKey("survey_responses.id"))

    question_id = Column(Integer, ForeignKey("survey_questions.id"))

    score = Column(Integer)

    comment = Column(String)

    response = relationship("SurveyResponse")


# -------------------------
# Assignment
# -------------------------

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_code = Column(String, ForeignKey("projects.project_code"), nullable=False)
    user_email = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    project = relationship(
        "Project",
        primaryjoin="Assignment.project_code == Project.project_code",
        foreign_keys="Assignment.project_code",
    )


# -------------------------
# Role
# -------------------------

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)


# -------------------------
# Permission
# -------------------------

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False)


# -------------------------
# RolePermission  (FK normalizada)
# -------------------------

class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )


# -------------------------
# LegalEntity
# -------------------------

class LegalEntity(Base):
    __tablename__ = "legal_entities"

    id   = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)


# -------------------------
# UserLegalEntity
# -------------------------

class UserLegalEntity(Base):
    __tablename__ = "user_legal_entities"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    legal_entity_id = Column(Integer, ForeignKey("legal_entities.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "legal_entity_id", name="uq_user_legal_entity"),
    )