from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

from surveycore_api.models import Base, User, MasterQuestion, QuestionTranslation, QuestionOption, OptionTranslation, Project, Survey, SurveyQuestion, SurveyRecipient, SurveyAccess, SurveyResponse, SurveyAnswer
from surveycore_api.auth.password import get_password_hash

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./survey.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

print("Tables created")


# USERS
user1 = User(
    name="Ana Quality",
    email="ana@gft.com",
    hashed_password=get_password_hash("password123"),
    role="QUALITY"
)
user2 = User(
    name="Carlos Delivery",
    email="carlos@gft.com",
    hashed_password=get_password_hash("password123"),
    role="DELIVERY"
)

session.add_all([user1, user2])
session.commit()


# QUESTIONS DATA
questions_data = [

{
"logical_code": "COMMUNICATION_CLARITY",
"type": "RATING",
"en": "How clear was the communication during the project?",
"es": "¿Qué tan clara fue la comunicación durante el proyecto?",
"de": "Wie klar war die Kommunikation während des Projekts?"
},

{
"logical_code": "DELIVERY_TIMELINESS",
"type": "RATING",
"en": "How satisfied are you with delivery timelines?",
"es": "¿Qué tan satisfecho está con los tiempos de entrega?",
"de": "Wie zufrieden sind Sie mit den Lieferzeiten?"
},

{
"logical_code": "TEAM_COLLABORATION",
"type": "RATING",
"en": "How effective was the collaboration with the team?",
"es": "¿Qué tan efectiva fue la colaboración con el equipo?",
"de": "Wie effektiv war die Zusammenarbeit mit dem Team?"
},

{
"logical_code": "TECHNICAL_EXPERTISE",
"type": "RATING",
"en": "How would you rate the technical expertise of the team?",
"es": "¿Cómo calificaría la experiencia técnica del equipo?",
"de": "Wie bewerten Sie die technische Expertise des Teams?"
},

{
"logical_code": "PROJECT_MANAGEMENT",
"type": "RATING",
"en": "How satisfied are you with project management?",
"es": "¿Qué tan satisfecho está con la gestión del proyecto?",
"de": "Wie zufrieden sind Sie mit dem Projektmanagement?"
},

{
"logical_code": "RECOMMENDATION",
"type": "RATING",
"en": "How likely are you to recommend our services?",
"es": "¿Qué tan probable es que recomiende nuestros servicios?",
"de": "Wie wahrscheinlich ist es, dass Sie unsere Dienstleistungen empfehlen?"
},

{
"logical_code": "COMMUNICATION_CHANNEL",
"type": "DROPDOWN",
"en": "Preferred communication channel?",
"es": "¿Canal de comunicación preferido?",
"de": "Bevorzugter Kommunikationskanal?",
"options": ["Email","Slack","Teams","Phone"]
},

{
"logical_code": "PROJECT_COMPLEXITY",
"type": "DROPDOWN",
"en": "How complex was the project?",
"es": "¿Qué tan complejo fue el proyecto?",
"de": "Wie komplex war das Projekt?",
"options": ["Low","Medium","High"]
},

{
"logical_code": "SERVICE_USED",
"type": "DROPDOWN",
"en": "Which service did you use?",
"es": "¿Qué servicio utilizó?",
"de": "Welchen Service haben Sie genutzt?",
"options": ["Consulting","Development","Support"]
},

{
"logical_code": "COUNTRY_CLIENT",
"type": "DROPDOWN",
"en": "Client country",
"es": "País del cliente",
"de": "Land des Kunden",
"options": ["Germany","Spain","Brazil","USA","Colombia"]
},

{
"logical_code": "TOOLS_USED",
"type": "MULTI_SELECT",
"en": "Which tools were used in the project?",
"es": "¿Qué herramientas se usaron en el proyecto?",
"de": "Welche Tools wurden im Projekt verwendet?",
"options": ["Jira","Azure DevOps","GitHub","Slack","Teams"]
},

{
"logical_code": "TECH_STACK",
"type": "MULTI_SELECT",
"en": "Technologies used",
"es": "Tecnologías utilizadas",
"de": "Verwendete Technologien",
"options": ["Python","Java",".NET","SQL","Cloud"]
},

{
"logical_code": "PROJECT_CHALLENGES",
"type": "TEXT",
"en": "What were the main challenges?",
"es": "¿Cuáles fueron los principales desafíos?",
"de": "Was waren die größten Herausforderungen?"
},

{
"logical_code": "PROJECT_SUCCESS",
"type": "TEXT",
"en": "What contributed most to project success?",
"es": "¿Qué contribuyó más al éxito del proyecto?",
"de": "Was hat am meisten zum Projekterfolg beigetragen?"
},

{
"logical_code": "IMPROVEMENTS",
"type": "TEXT",
"en": "What could we improve?",
"es": "¿Qué podríamos mejorar?",
"de": "Was können wir verbessern?"
},

{
"logical_code": "CLIENT_FEEDBACK",
"type": "TEXT",
"en": "Additional feedback",
"es": "Comentarios adicionales",
"de": "Zusätzliches Feedback"
},

{
"logical_code": "PROJECT_DURATION",
"type": "DROPDOWN",
"en": "Project duration",
"es": "Duración del proyecto",
"de": "Projektdauer",
"options": ["<3 months","3-6 months","6-12 months",">12 months"]
},

{
"logical_code": "TEAM_SIZE",
"type": "DROPDOWN",
"en": "Team size",
"es": "Tamaño del equipo",
"de": "Teamgröße",
"options": ["1-3","4-7","8-15","15+"]
},

{
"logical_code": "SATISFACTION_OVERALL",
"type": "RATING",
"en": "Overall satisfaction with the project",
"es": "Satisfacción general con el proyecto",
"de": "Gesamtzufriedenheit mit dem Projekt"
},

{
"logical_code": "RETURN_CLIENT",
"type": "DROPDOWN",
"en": "Would you work with us again?",
"es": "¿Trabajaría con nosotros nuevamente?",
"de": "Würden Sie wieder mit uns arbeiten?",
"options": ["Yes","No","Maybe"]
}

]


# INSERT QUESTIONS

for i, q in enumerate(questions_data):

    status = "PUBLISHED" if i < 10 else "DRAFT"

    question = MasterQuestion(
        logical_code=q["logical_code"],
        status=status,
        answer_type=q["type"],
        created_by=user1.id,
        created_at=datetime.utcnow(),
        published_at=datetime.utcnow() if status == "PUBLISHED" else None
    )

    session.add(question)
    session.commit()

    translations = [

        QuestionTranslation(
            master_question_id=question.id,
            language_code="EN",
            question_text=q["en"],
            is_default_language=True
        ),

        QuestionTranslation(
            master_question_id=question.id,
            language_code="ES",
            question_text=q["es"],
            is_default_language=False
        ),

        QuestionTranslation(
            master_question_id=question.id,
            language_code="DEU",
            question_text=q["de"],
            is_default_language=False
        )

    ]

    session.add_all(translations)

    if "options" in q:

        for opt in q["options"]:

            option = QuestionOption(
                master_question_id=question.id,
                option_text=opt
            )

            session.add(option)
            session.commit()

            session.add_all([
                OptionTranslation(option_id=option.id, language_code="EN", option_text=opt),
                OptionTranslation(option_id=option.id, language_code="ES", option_text=opt),
                OptionTranslation(option_id=option.id, language_code="DEU", option_text=opt)
            ])

    session.commit()


print("Database created and seeded with 20 questions.")

project1 = Project(
    project_code="PRJ-1001",
    project_name="Digital Banking Platform",
    client_name="Global Bank",
    cost_center="CC100",
    manager_id=user2.id,
    status="ACTIVE"
)

project2 = Project(
    project_code="PRJ-1002",
    project_name="Retail Data Warehouse",
    client_name="RetailCorp",
    cost_center="CC200",
    manager_id=user2.id,
    status="ACTIVE"
)

session.add_all([project1, project2])
session.commit()

print("Projects seeded.")

survey1 = Survey(
    project_id=project1.id,
    survey_type="Quarterly",
    language_code="EN",
    created_by=user2.id,
    survey_status="DRAFT"
)

session.add(survey1)
session.commit()

print("Survey seeded.")

recipient1 = SurveyRecipient(
    survey_id=survey1.id,
    recipient_name="John Smith",
    recipient_email="john.smith@globalbank.com",
    company="Global Bank",
    role="CTO"
)

recipient2 = SurveyRecipient(
    survey_id=survey1.id,
    recipient_name="Anna Müller",
    recipient_email="anna.mueller@globalbank.com",
    company="Global Bank",
    role="Delivery Lead"
)

session.add_all([recipient1, recipient2])
session.commit()

print("SurveyRecipient seeded.")