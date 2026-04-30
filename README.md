# surveycore-api

REST API for SurveyCore — multi-language survey management with role-based access control and Microsoft Entra ID SSO.

**Deployed on:** [Render.com](https://surveycore-api.onrender.com)

## Stack

| | |
|---|---|
| **Framework** | FastAPI 0.109 · Python 3.13 |
| **ORM** | SQLAlchemy 2.0 |
| **Database** | PostgreSQL on Neon (all environments) |
| **Auth** | JWT HS256 · Microsoft Entra ID (JWKS) |
| **Deployment** | Render.com (qa branch) |

---

## Quick Start (Local Development)

```bash
# 1. Clone and enter repo
git clone https://github.com/everprieto/surveycore-api.git
cd surveycore-api
git checkout dev

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your Neon PostgreSQL connection string

# 5. Seed database (first time only)
python init_db.py

# 6. Run
uvicorn surveycore_api.main:app --reload --port 8000
```

API: **http://localhost:8000** · Swagger: **http://localhost:8000/docs** · Health: **/health**

---

## Project Structure

```
surveycore-api/
├── surveycore_api/           ← Python package
│   ├── main.py               # FastAPI app, CORS, router registration
│   ├── models.py             # SQLAlchemy ORM (15 models)
│   ├── database.py           # Engine + SessionLocal (reads DATABASE_URL)
│   ├── dependencies.py       # get_db() session injection
│   ├── utils.py              # Token generation helpers
│   ├── auth/                 # JWT, JWKS, permissions
│   │   ├── jwt_handler.py
│   │   ├── deps.py
│   │   ├── microsoft.py
│   │   └── password.py
│   ├── routers/              # API endpoints
│   │   ├── auth.py
│   │   ├── questions.py
│   │   ├── projects.py
│   │   ├── surveys.py
│   │   ├── public.py
│   │   ├── results.py
│   │   └── admin.py
│   └── schemas/              # Pydantic models
│       ├── auth.py
│       ├── question.py
│       ├── project.py
│       ├── survey.py
│       └── response.py
├── init_db.py                # Database seed script
├── setup.py                  # Package setup for pip install -e .
├── requirements.txt          # Python dependencies
├── Procfile                  # Gunicorn + Uvicorn configuration
├── render.yaml               # Render.com deployment blueprint
├── .env.example              # Local dev template
├── .env.qa.example           # QA environment template
├── .env.production.example   # Production template
├── CLAUDE.md                 # Backend development guide
├── SETUP_LOCAL.md            # Local setup instructions
├── NEON_SETUP.md             # PostgreSQL/Neon guide
├── RENDER_SETUP.md           # Render.com deployment guide
└── .gitignore
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL on Neon | `postgresql+psycopg://user:pass@host/db?sslmode=require` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `480` |
| `CORS_ORIGINS` | Allowed frontend URLs | `http://localhost:5173,https://example.azurestaticapps.net` |
| `AZURE_TENANT_ID` | Entra ID tenant | `0a964db6-c0c3-43a8-af0d-bccc2d2bd487` |
| `AZURE_CLIENT_ID` | Entra ID app ID | `4012c112-0db8-4411-85e5-907edceb644e` |
| `AZURE_CLIENT_SECRET` | Entra ID secret | (keep in .env, never commit) |

---

## API Endpoints

| Router | Prefix | Auth | Purpose |
|---|---|---|---|
| **Auth** | `/auth` | public/JWT | Login, register, SSO, user info |
| **Questions** | `/questions` | JWT | Question library CRUD + translations |
| **Projects** | `/projects` | JWT | Project management |
| **Surveys** | `/surveys` | JWT | Survey creation and configuration |
| **Results** | `/results` | JWT | Survey responses and analytics |
| **Admin** | `/admin` | JWT+admin | System administration |
| **Public** | `/public` | none | Token-based survey access |

See [CLAUDE.md](./CLAUDE.md) for full endpoint documentation.

---

## Database Seeding

```bash
python init_db.py
```

Default credentials:
| Email | Password | Role |
|---|---|---|
| ana@gft.com | password123 | ADMIN |
| carlos@gft.com | password123 | SURVEY_MANAGER |

---

## Deployment

### Local → QA (Render.com)

```bash
git checkout qa
git merge dev
git push origin qa
# Render auto-deploys to https://surveycore-api.onrender.com
```

See [RENDER_SETUP.md](./RENDER_SETUP.md) for complete Render deployment guide.

### Branch Strategy

| Branch | Environment | Deployment |
|---|---|---|
| `dev` | Local | `http://localhost:8000` |
| `qa` | QA | `https://surveycore-api.onrender.com` |
| `main` | Production | `https://surveycore-api.onrender.com` |

All branches use PostgreSQL on Neon.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'surveycore_api'` | Run `pip install -e .` to install local package |
| `DATABASE_URL not found` | Check `.env` file exists and has DATABASE_URL |
| CORS errors from frontend | Verify frontend URL in `CORS_ORIGINS` environment variable |
| Import errors in routers | Ensure `__init__.py` exists in all package directories |

See [NEON_SETUP.md](./NEON_SETUP.md) and [CLAUDE.md](./CLAUDE.md) for more help.
