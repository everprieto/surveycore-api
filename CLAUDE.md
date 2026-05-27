# SurveyCore API Agent — SurveyCore

Agente especializado en la API de SurveyCore.  
Stack: **FastAPI 0.109 · SQLAlchemy 2.0 · Python 3.13 · PostgreSQL on Neon**

---

## Levantar la API

```bash
# Desde la raíz del repo (surveycore-api/)
# Asegurar que .venv está activado
python -m uvicorn surveycore_api.main:app --reload --port 8000
```

API disponible en `http://localhost:8000`  
Swagger: `http://localhost:8000/docs` · ReDoc: `/redoc` · OpenAPI Schema: `/openapi.json`  
Health check: `GET /health`

---

## Estructura de Archivos

```
surveycore-api/               ← raíz del repo git
├── surveycore_api/           ← paquete Python
│   ├── main.py               # Entrypoint: app FastAPI, CORS, registro de routers
│   ├── models.py             # SQLAlchemy ORM — 15 modelos
│   ├── database.py           # Engine + SessionLocal (lee DATABASE_URL de .env)
│   ├── dependencies.py       # get_db() — inyección de sesión
│   ├── utils.py              # Utilidades: token generation, helpers
│   │
│   ├── auth/
│   │   ├── jwt_handler.py    # create_access_token / decode_access_token
│   │   ├── deps.py           # get_current_user / get_optional_user / get_admin_user
│   │   ├── password.py       # get_password_hash / verify_password
│   │   └── microsoft.py      # Validación tokens Microsoft Entra ID (JWKS)
│   │
│   ├── routers/
│   │   ├── auth.py           # POST /auth/login, /register, /microsoft | GET /auth/me
│   │   ├── questions.py      # CRUD /questions/ + traducciones + publicación
│   │   ├── projects.py       # CRUD /projects/
│   │   ├── surveys.py        # CRUD /surveys/ + preguntas + destinatarios
│   │   ├── public.py         # GET/POST /public/survey/{token} — sin auth
│   │   ├── results.py        # GET /results/survey/{id} — analytics
│   │   ├── admin.py          # Endpoints administrativos
│   │   └── emails.py         # Envío de emails (Azure Communication Service)
│   │
│   └── schemas/
│       ├── auth.py           # UserLogin, UserRegister, Token, UserResponse
│       ├── question.py       # QuestionCreate/Update/Response, Translation*, Option*
│       ├── survey.py         # SurveyCreate/Update/Response, RecipientCreate, AccessLink
│       ├── project.py        # ProjectCreate/Update/Response
│       └── response.py       # SurveyResponse, AnswerSubmit, SurveySubmit
├── init_db.py                # Seed script — run from repo root
├── setup.py                  # Package setup (version 2.0.0)
├── requirements.txt          # pip dependencies
├── Procfile                  # Azure App Service: gunicorn + uvicorn workers
├── startup.sh                # Azure deployment script
├── .env.example              # Local development
├── .env.qa.example           # QA environment
├── .env.production.example   # Production environment
└── .gitignore
```

---

## Endpoints por Router

### Auth — `/auth`
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Crear usuario con email/password |
| POST | `/auth/login` | No | Login → JWT token |
| POST | `/auth/microsoft` | No | SSO Microsoft Entra ID → JWT |
| GET | `/auth/me` | JWT | Usuario actual (validar token) |

### Questions — `/questions`
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/questions/` | JWT | Listar todas |
| POST | `/questions/` | JWT | Crear (DRAFT) |
| GET | `/questions/{id}` | JWT | Detalle con traducciones |
| PUT | `/questions/{id}` | JWT | Editar (solo DRAFT) |
| POST | `/questions/{id}/publish` | JWT | Publicar → PUBLISHED (inmutable) |
| POST | `/questions/{id}/translations` | JWT | Añadir traducción |
| POST | `/questions/options/translations` | JWT | Traducir opción |

### Projects — `/projects`
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/projects/` | JWT | Proyectos del usuario |
| GET | `/projects/all` | JWT | Todos los proyectos |
| GET | `/projects/{id}` | JWT | Detalle |
| POST | `/projects/` | JWT | Crear proyecto |
| PUT | `/projects/{id}` | JWT | Actualizar |

### Surveys — `/surveys`
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/surveys/types` | Public | Obtener tipos de encuesta disponibles |
| POST | `/surveys/` | JWT | Crear encuesta (requiere `survey_type_id`) |
| GET | `/surveys/{id}` | JWT | Configuración completa |
| PUT | `/surveys/{id}` | JWT | Actualizar (incluye `survey_type_id`) |
| POST | `/surveys/{id}/questions` | JWT | Añadir pregunta |
| DELETE | `/surveys/{id}/questions/{sq_id}` | JWT | Quitar pregunta |
| PATCH | `/surveys/{id}/questions/{sq_id}` | JWT | Actualizar pregunta |
| POST | `/surveys/{id}/recipients` | JWT | Añadir destinatario |
| DELETE | `/surveys/{id}/recipients/{id}` | JWT | Quitar destinatario |
| POST | `/surveys/{id}/generate-links` | JWT | Generar tokens de acceso |
| POST | `/surveys/{id}/send-emails` | JWT | Enviar emails con links |
| GET | `/surveys/{id}/preview` | JWT | Vista previa de encuesta |

### Public — `/public` (sin autenticación)
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/public/survey/{token}` | No | Obtener encuesta por token de acceso |
| POST | `/public/survey/{token}/submit` | No | Enviar respuestas sin auth |

### Email — `/email` (interno)
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/email/send-survey-link` | JWT | Enviar encuesta por correo |
| POST | `/email/send-reminder` | JWT | Recordatorio de encuesta |

---

## Modelos ORM (models.py)

```
User               — id, name, email, hashed_password, role_id
Role               — id, name, description, is_system
Permission         — id, code, description
RolePermission     — id, role_id, permission_id (M:N)
LegalEntity        — id, name
UserLegalEntity    — id, user_id, legal_entity_id (M:N)
MasterQuestion     — id, logical_code, answer_type, status (DRAFT/PUBLISHED), created_by, created_at
QuestionTranslation— id, master_question_id, language_code, question_text, is_default_language
QuestionOption     — id, master_question_id, option_text
OptionTranslation  — id, option_id, language_code, option_text
Project            — id, project_code, project_name, manager_id, legal_entity_id, status
SurveyType         — id, survey_type (String, unique) ← NEW
Survey             — id, project_id, survey_type_id (FK→SurveyType), language_code, survey_status, created_by
SurveyQuestion     — id, survey_id, master_question_id, display_order, is_required
SurveyRecipient    — id, survey_id, recipient_name, recipient_email, company, role
SurveyAccess       — id, survey_id, recipient_id, access_token, status (PENDING/OPENED/COMPLETED)
SurveyResponse     — id, survey_access_id, submitted_at
SurveyAnswer       — id, response_id, question_id, score, comment
Assignment         — id, project_code, user_email, start_date, end_date
AuditLog           — definido, no usado actualmente
```

---

## Patrones de Implementación

### Nueva ruta
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..auth.deps import get_current_user
from ..models import MyModel
from ..schemas.myschema import MyCreate, MyResponse

router = APIRouter(prefix="/myresource", tags=["myresource"])

@router.get("/", response_model=list[MyResponse])
def list_items(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(MyModel).all()

@router.post("/", response_model=MyResponse, status_code=201)
def create_item(data: MyCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = MyModel(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
```

### Ruta pública (sin auth)
```python
@router.get("/public/{token}")
def public_endpoint(token: str, db: Session = Depends(get_db)):
    # Sin get_current_user
    ...
```

### Recurso no encontrado
```python
item = db.get(MyModel, id)
if not item:
    raise HTTPException(status_code=404, detail="Not found")
```

### Sesión DB — SIEMPRE con Depends
```python
# CORRECTO
def my_route(db: Session = Depends(get_db)): ...

# INCORRECTO — no crear sesiones manualmente
db = SessionLocal()
```

---

## Autenticación

**JWT Handler** (`auth/jwt_handler.py`)
- Algoritmo: HS256
- Expiración: 480 min (configurable en `.env`)
- `create_access_token(data: dict)` → token string
- `decode_access_token(token: str)` → payload dict

**Dependency** (`auth/deps.py`)
- `get_current_user` → HTTPBearer, lanza 401 si token inválido
- `get_optional_user` → devuelve None si no hay token

**Microsoft Entra ID** (`auth/microsoft.py`)
- Valida `id_token` contra JWKS de Microsoft
- Auto-provisiona usuario en primer login
- Variables: `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`

---

## Variables de Entorno (`.env` raíz)

```
SECRET_KEY=<mín 32 chars>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
DATABASE_URL=postgresql+psycopg://neondb_owner:password@host-pooler:5432/surveycore_qa?sslmode=require&channel_binding=require
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
AZURE_TENANT_ID=0a964db6-c0c3-43a8-af0d-bccc2d2bd487
AZURE_CLIENT_ID=571c0742-cd9d-4b30-9c88-692a4e7c37fa
AZURE_CLIENT_SECRET=<secret>
```

---

## Reglas de Negocio Críticas

1. **Preguntas PUBLISHED son inmutables** — PUT lanza HTTP 403 si `status == PUBLISHED`
2. **Solo preguntas PUBLISHED** pueden añadirse a encuestas
3. **display_order** en SurveyQuestion: siempre `COUNT(existentes) + 1`
4. **Token único por destinatario**: `secrets.token_hex(16)` → 32 chars hex
5. **Fallback de idioma**: intentar `language_code` de la encuesta → si no existe, usar `is_default_language=True`
6. **MULTI_SELECT**: almacenar como string separado por comas en `SurveyAnswer.comment`

---

## Testing

```bash
# Smoke test rápido
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health

# Con token
curl -s -H "Authorization: Bearer <token>" http://localhost:8000/auth/me

# Ver respuesta
curl -s http://localhost:8000/questions/ | python -m json.tool | head -40
```

---

## Problemas Frecuentes

| Problema | Solución |
|----------|----------|
| `python-multipart` no instalado | `pip install python-multipart` |
| Session leak | Usar `Depends(get_db)`, nunca `SessionLocal()` directo |
| 422 Unprocessable Entity | Revisar tipos en schemas Pydantic vs payload enviado |
| CORS error desde frontend | Verificar `CORS_ORIGINS` en `.env` incluye el puerto de Vite |
| JWT inválido | Verificar `SECRET_KEY` y `ALGORITHM` coinciden con el token generado |
| Microsoft SSO falla | Verificar `AZURE_TENANT_ID` / `AZURE_CLIENT_ID` en `.env` |
