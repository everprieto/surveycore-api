# GitHub Setup — Backend Deployment

This document describes how to configure GitHub Secrets for automated backend deployments to Azure.

## Required Secrets

Configure these secrets in your GitHub repository settings → Secrets and variables → Actions:

### Azure Secrets (2 required)
| Secret Name | Value | Source |
|-------------|-------|--------|
| `AZURE_PUBLISH_PROFILE_QA` | QA App Service publish profile (XML) | Azure Portal |
| `AZURE_PUBLISH_PROFILE_PRODUCTION` | Production App Service publish profile (XML) | Azure Portal |

### Neon Secrets (2 required)
| Secret Name | Value | Source |
|-------------|-------|--------|
| `NEON_DATABASE_URL_QA` | QA PostgreSQL connection string | Neon Console |
| `NEON_DATABASE_URL_PRODUCTION` | Production PostgreSQL connection string | Neon Console |

**Total: 4 secrets to configure**

## How to Get Secrets

### Azure Publish Profiles

#### 1. From Azure Portal — QA Environment
- Go to **Azure Portal** → search **surveycore-api-qa** (App Service)
- Click **Get publish profile** (download button at top)
- Copy the entire XML content
- In GitHub → **Settings** → **Secrets and variables** → **Actions**
- Click **New repository secret**
- Name: `AZURE_PUBLISH_PROFILE_QA`
- Value: (paste the XML)
- Click **Add secret**

#### 2. From Azure Portal — Production Environment
- Go to **Azure Portal** → search **surveycore-api** (App Service)
- Click **Get publish profile** (download button at top)
- Copy the entire XML content
- In GitHub → **Settings** → **Secrets and variables** → **Actions**
- Click **New repository secret**
- Name: `AZURE_PUBLISH_PROFILE_PRODUCTION`
- Value: (paste the XML)
- Click **Add secret**

### Neon PostgreSQL Connection Strings

#### 3. From Neon Console — QA Database

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
