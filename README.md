# surveycore-api

REST API for SurveyCore — multi-language survey management with role-based access control and Microsoft Entra ID SSO.

## Stack

| | |
|---|---|
| **Framework** | FastAPI 0.109 · Python 3.13 |
| **ORM** | SQLAlchemy 2.0 |
| **Database** | SQLite (dev) · PostgreSQL (prod) |
| **Auth** | JWT HS256 · Microsoft Entra ID (JWKS) |

---

## Quick Start

```bash
# 1. Clone and enter repo
git clone <url> surveycore-api
cd surveycore-api

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your values

# 5. Seed database (first time only)
python init_db.py

# 6. Run
uvicorn surveycore_api.main:app --reload --port 8000
```

API: **http://localhost:8000** · Swagger: **http://localhost:8000/docs**

---

## Project Structure

```
surveycore-api/
├── surveycore_api/       ← Python package
│   ├── main.py           # FastAPI app, CORS, router registration
│   ├── models.py         # SQLAlchemy ORM (15 models)
│   ├── database.py       # Engine + SessionLocal (reads DATABASE_URL)
│   ├── dependencies.py   # get_db() session injection
│   ├── utils.py          # Token generation helpers
│   ├── auth/             # JWT, JWKS, permissions
│   ├── routers/          # auth, questions, projects, surveys, public, results, admin
│   └── schemas/          # Pydantic request/response models
├── init_db.py            # DB seed script
├── startup.sh            # Azure App Service startup
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Min 32 chars — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | `sqlite:///./survey.db` for dev, PostgreSQL URL for prod |
| `CORS_ORIGINS` | Comma-separated allowed origins (e.g. `http://localhost:5173`) |
| `AZURE_TENANT_ID` | Entra ID tenant — optional, only needed for SSO |
| `AZURE_CLIENT_ID` | Entra ID client — optional, only needed for SSO |

---

## API Endpoints

| Router | Prefix | Auth |
|---|---|---|
| Auth | `/auth` | Public (login/register) · JWT (me) |
| Questions | `/questions` | JWT + permissions |
| Projects | `/projects` | JWT + permissions |
| Surveys | `/surveys` | JWT + permissions |
| Results | `/results` | JWT + permissions |
| Admin | `/admin` | JWT + admin role |
| Public | `/public` | No auth (token-based) |

---

## Default Seed Credentials

| Email | Password | Role |
|---|---|---|
| ana@gft.com | password123 | ADMIN |
| carlos@gft.com | password123 | SURVEY_MANAGER |

> Run `python init_db.py` to create and seed the database.

---

## Azure Deployment

Configure Azure App Service startup command:
```bash
bash startup.sh
```

See `DEPLOYMENT.md` in the root workspace for full Azure deployment guide.
