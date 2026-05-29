# Local Development Setup — Backend

## Prerequisites

- Python 3.14.5 (check with `python --version`)
- pip / venv

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd surveycore-api
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` from template**
   ```bash
   cp .env.example .env
   ```

5. **Run the API**
   ```bash
   uvicorn surveycore_api.main:app --reload --port 8000
   ```

   API will be available at `http://localhost:8000`
   - Swagger docs: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Environment Variables

The `.env` file (created above) contains:

```
SECRET_KEY=change-me-min-32-chars-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
DATABASE_URL=postgresql+psycopg://user:password@host:port/database?sslmode=require&channel_binding=require
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
```

### For Microsoft Entra ID SSO (optional):
Replace empty Azure values:
- `AZURE_TENANT_ID`: Your Azure Tenant ID
- `AZURE_CLIENT_ID`: Your Azure App Registration Client ID
- `AZURE_CLIENT_SECRET`: Your Azure App Registration Client Secret

Leave blank if you're using email/password auth only.

## Database

The API uses **PostgreSQL on Neon** for all environments (local, QA, production).

Update `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql+psycopg://user:password@host:port/database?sslmode=require&channel_binding=require
```

Tables are auto-created on startup. Get your Neon connection string from: https://console.neon.tech → Projects → Connection string

To reset the database in Neon, use the SQL Editor or connect with `psql` and drop/recreate tables as needed.

## Common Commands

### Run tests (if available)
```bash
pytest
```

### Format code
```bash
black surveycore_api
```

### Lint
```bash
flake8 surveycore_api
```

### Seed sample data (if available)
```bash
python init_db.py
```

## Frontend Integration

When running the frontend locally:

1. **Frontend** runs on `http://localhost:5173` (Vite)
2. **Backend** runs on `http://localhost:8000` (uvicorn)

Frontend `.env`:
```
VITE_API_BASE_URL=http://localhost:8000
```

Backend `.env` already includes this in `CORS_ORIGINS`.

If you get CORS errors:
- Check `CORS_ORIGINS` in backend `.env`
- Verify frontend is using correct `VITE_API_BASE_URL`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'surveycore_api'` | Ensure you're in the repo root and have activated venv |
| `Address already in use :8000` | Another app is using port 8000. Use `--port 9000` instead |
| `DATABASE_URL not found` | Create `.env` from `.env.example` with valid Neon PostgreSQL connection string |
| CORS error from frontend | Update `CORS_ORIGINS` in `.env` to include frontend URL |
| `psycopg connection refused` | Verify DATABASE_URL is correct and Neon is accessible |
| `too many connections` | Neon pool limit reached; close unused connections or upgrade plan |

## Documentation

For detailed API documentation, see:
- `CLAUDE.md` — architecture, models, endpoints, patterns
- Swagger UI at `http://localhost:8000/docs`
