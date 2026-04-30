# GitHub Setup — Backend (surveycore-api)

## Overview

The backend uses **Render.com for deployment**. Render connects directly to GitHub and deploys via `render.yaml` — **no GitHub Secrets or Actions workflows are needed**.

Deployment happens automatically:
1. Push to `qa` branch → Render detects push and redeployment
2. Render reads `render.yaml` from the repository
3. Render creates/updates PostgreSQL database and environment variables
4. Render builds and deploys the application

## Branches & Deployment

| Branch | Platform | URL | Auto-Deploy |
|--------|----------|-----|-------------|
| `dev` | Local | `http://localhost:8000` | N/A |
| `qa` | Render.com | `https://surveycore-api.onrender.com` | Yes ✅ |
| `main` | Render.com | `https://surveycore-api.onrender.com` | Yes ✅ |

## GitHub Configuration

### 1. Connect Render to GitHub

1. Go to https://render.com/dashboard
2. Click **New +** → **Web Service**
3. Select **Build and deploy from a Git repository**
4. Click **Connect account** and authenticate with GitHub
5. Select your `surveycore-api` repository
6. Select branch: `qa`
7. Render will auto-detect `render.yaml`
8. Click **Create Web Service**

Render will automatically:
- Create PostgreSQL database (surveycore-qa-db)
- Configure environment variables from `render.yaml`
- Deploy the application

### 2. Environment Variables in Render

Variables are configured in `render.yaml` or Render dashboard:

| Variable | Auto-Generated | Manual |
|----------|---|---|
| `DATABASE_URL` | ✅ From database connection | - |
| `SECRET_KEY` | ✅ Auto-generated | - |
| `PYTHON_VERSION` | - | ✅ `render.yaml` |
| `AZURE_TENANT_ID` | - | ✅ `render.yaml` |
| `AZURE_CLIENT_ID` | - | ✅ `render.yaml` |
| `AZURE_CLIENT_SECRET` | - | ✅ Manual in Render dashboard |
| `CORS_ORIGINS` | - | ✅ `render.yaml` |

### 3. Update CORS Origins

When deploying frontend to Azure Static Web Apps:

1. Update `render.yaml` → `CORS_ORIGINS`:
   ```yaml
   value: https://surveycore-qa.onrender.com,https://[YOUR-AZURE-URL].azurestaticapps.net,http://localhost:5173
   ```

2. Push to `qa`:
   ```bash
   git push origin qa
   ```

3. Render auto-redeploys with updated CORS configuration

## No GitHub Secrets Required

Since Render doesn't use GitHub Actions:
- ❌ No GitHub Secrets needed for backend deployment
- ❌ No workflow files (.github/workflows/) needed
- ✅ Use `render.yaml` for infrastructure as code

## Monitoring

Monitor deployments in **Render dashboard**:
1. Go to https://render.com/dashboard
2. Click on `surveycore-api-qa`
3. View **Logs** tab for build/deployment output
4. View **Metrics** tab for CPU, memory, requests

## Troubleshooting

| Issue | Solution |
|---|---|
| Deployment fails: "render.yaml not found" | Ensure `render.yaml` is in repository root and committed |
| Database connection fails | Check `DATABASE_URL` in Render environment variables |
| Import errors after deploy | Ensure `setup.py` exists and `requirements.txt` has `-e .` |
| Environment variable not updated | Render may need manual save in dashboard if using UI |

1. Go to [https://console.neon.tech](https://console.neon.tech)
2. Select your project
3. From the dashboard, copy the **Connection String** (top right button)
4. This shows: `postgresql://user:password@host:port/database?sslmode=require`
5. If you created a separate `surveycore_qa` database, ensure the connection string uses that database name
6. In GitHub → **Settings** → **Secrets and variables** → **Actions**
7. Click **New repository secret**
8. Name: `NEON_DATABASE_URL_QA`
9. Value: (paste the full connection string)
10. Click **Add secret**

#### 4. From Neon Console — Production Database

1. Go to [https://console.neon.tech](https://console.neon.tech)
2. Select your project
3. From the dashboard, copy the **Connection String** (for production database)
4. If you created a separate `surveycore_prod` database, ensure the connection string uses that database name
5. In GitHub → **Settings** → **Secrets and variables** → **Actions**
6. Click **New repository secret**
7. Name: `NEON_DATABASE_URL_PRODUCTION`
8. Value: (paste the full connection string)
9. Click **Add secret**

**⚠️ Security Note:** Connection strings contain passwords. Never commit them to Git. Always use GitHub Secrets.

## Verification

Once secrets are added:
1. Go to your GitHub repository
2. Click **Actions** tab
3. Push to `qa` or `main` branch to trigger deployment
4. Monitor the workflow run for success/failure

If the workflow fails, check:

**Azure Errors:**
- Publish profile XML is valid (no truncation or extra spaces)
- App Service names in `deploy.yml` match Azure resources (`surveycore-api-qa`, `surveycore-api`)
- App Service is in the same region where resources exist

**Neon Errors:**
- Connection string format: `postgresql://user:password@host:port/database?sslmode=require`
- Database name matches your Neon setup
- Password hasn't been changed (regenerate if needed in Neon console)

## Environment Variables in Azure

The workflow creates a `.env` file and injects secrets. Some values in `.env.*.example` are still placeholders:
- `AZURE_CLIENT_SECRET` — set in Azure Portal or GitHub Secret
- `SECRET_KEY` — should be a secure random string (configure separately)

### To update additional environment variables in Azure Portal:
1. Go to **Azure Portal** → App Service resource (qa or production)
2. Click **Settings** → **Configuration** → **Application settings**
3. Click **+ New application setting** for each new variable
4. Examples:
   - Name: `AZURE_CLIENT_SECRET` | Value: (your client secret)
   - Name: `SECRET_KEY` | Value: (secure random 32+ char string)
5. Click **Save** at the top

Restart the App Service for changes to take effect.

For sensitive values, prefer GitHub Secrets over Azure Portal settings.

## Deployment Flow

1. Developer pushes to `qa` or `main` branch
2. GitHub Actions workflow triggers
3. Python dependencies are installed and linted
4. `.env.qa.example` or `.env.production.example` is copied to `.env`
5. Azure App Service deployment begins
6. App Service restarts with new code and environment variables
7. `startup.sh` runs: pip install, gunicorn + uvicorn start
8. API available at:
   - QA: `https://surveycore-api-qa.azurewebsites.net`
   - Production: `https://surveycore-api.azurewebsites.net`
