# Render.com Deployment Setup

This guide explains how to deploy surveycore-api to Render.com from the `qa` branch.

## Prerequisites

1. **GitHub Account**: Repository must be on GitHub (done ✅)
2. **Render.com Account**: Sign up at https://render.com
3. **Branch**: Use `qa` branch for QA deployments

## One-Click Deployment (Recommended)

If using `render.yaml`:

1. Go to https://render.com/
2. Click **New +** → **Web Service**
3. Select **Build and deploy from a Git repository**
4. Connect your GitHub account and select `everprieto/surveycore-api`
5. Select branch: `qa`
6. Render will auto-detect `render.yaml` and use it
7. Click **Create Web Service**

Render will automatically:
- Create a PostgreSQL database
- Configure environment variables
- Deploy the FastAPI app with Gunicorn + Uvicorn

## Manual Setup (if render.yaml doesn't auto-detect)

### 1. Create Web Service

1. Go to https://render.com/dashboard
2. Click **New +** → **Web Service**
3. Fill in:
   - **Name**: `surveycore-api-qa`
   - **Repository**: `https://github.com/everprieto/surveycore-api`
   - **Branch**: `qa`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn surveycore_api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120`
   - **Plan**: Free (or Starter)

4. Click **Create Web Service**

### 2. Create PostgreSQL Database

1. From Render dashboard, click **New +** → **PostgreSQL**
2. Fill in:
   - **Name**: `surveycore-qa-db`
   - **Database**: `surveycore_qa`
   - **User**: `surveycore_qa` (auto-generated)
   - **Region**: Same as web service
   - **Plan**: Free (or Standard)

3. Click **Create Database**

### 3. Connect Database to Web Service

1. Go back to your web service (`surveycore-api-qa`)
2. Click **Environment** (left menu)
3. Add environment variables:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | (Copy from database page) |
| `SECRET_KEY` | (Generate: `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` |
| `CORS_ORIGINS` | `https://surveycore-qa.onrender.com,http://localhost:5173` |
| `AZURE_TENANT_ID` | `0a964db6-c0c3-43a8-af0d-bccc2d2bd487` |
| `AZURE_CLIENT_ID` | `4012c112-0db8-4411-85e5-907edceb644e` |
| `AZURE_CLIENT_SECRET` | (Provide your secret) |

4. Click **Save Changes**

### 4. Deploy

1. Your web service will automatically redeploy when you push to `qa` branch
2. Monitor deployment in **Logs** tab
3. Once deployment completes, your API will be live at:
   ```
   https://surveycore-api-qa.onrender.com
   ```

## Connecting Frontend

Update your frontend `.env.qa.example`:

```
VITE_API_BASE_URL=https://surveycore-api-qa.onrender.com
```

Then deploy frontend to Render or Azure Static Web Apps with this URL.

## Database Connection String Format

The database URL from Render looks like:

```
postgresql://username:password@host:5432/database_name
```

SQLAlchemy requires:

```
postgresql+psycopg://username:password@host:5432/database_name?sslmode=require
```

Render automatically provides the correct format, but if you need to manually add it, update it to use `postgresql+psycopg://` instead of `postgresql://`.

## Logs and Monitoring

1. Go to **Logs** tab to see deployment logs
2. Go to **Metrics** tab to monitor CPU, memory, and requests
3. Render auto-scales on free tier (may sleep after 15 mins of inactivity)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Deploy fails: "No start command" | Ensure `Procfile` or `Start Command` is set correctly |
| Database connection fails | Verify `DATABASE_URL` in environment variables |
| 500 errors | Check logs for SQLAlchemy/psycopg errors |
| Free tier sleeping | Upgrade to Starter plan for always-on service |

## Cost

- **Web Service (Free)**: $0/month (with limitations)
- **PostgreSQL (Free)**: 256MB storage, auto-sleeps
- **Upgrade**: ~$7/month for always-on service

## Next Steps

1. Push to `qa` branch: `git push origin qa`
2. Go to Render and connect GitHub repository
3. Set environment variables
4. Monitor deployment in logs
5. Test API at `https://surveycore-api-qa.onrender.com/docs`
6. Update frontend to use this URL
