# Neon PostgreSQL Setup

This guide explains how to set up and use PostgreSQL on Neon for QA and production environments.

## What is Neon?

Neon is a serverless PostgreSQL platform. Key benefits:
- **No server management**: Neon handles scaling and backups
- **Branch support**: Create separate databases for dev/qa/production
- **Generous free tier**: Perfect for testing
- **Connection pooling**: Built-in for high-concurrency scenarios

## Getting Started

### 1. Create a Neon Project

1. Go to [https://console.neon.tech](https://console.neon.tech)
2. Sign up (free)
3. Create a new project (name: "surveycore" or similar)
4. Neon automatically creates:
   - A default branch: `main`
   - Database: `neondb`
   - User: `neondb_owner`
   - Password: (auto-generated, shown once)

### 2. Get Connection String

From Neon Console:
1. Click your project
2. Click **Connection String** (top right)
3. Copy the PostgreSQL connection string (shows password once)
4. Format: `postgresql://user:password@host:port/database?sslmode=require`

**⚠️ SECURITY**: Never commit your connection string to GitHub. Use GitHub Secrets instead.

## Multiple Databases (QA vs Production)

### Option A: Create Separate Branches in Neon

1. Neon Dashboard → Your Project → **Branches**
2. Click **Create branch**
3. Create `qa` branch (linked to main production database)
4. Get connection strings for each branch:
   - `main` branch: use for production
   - `qa` branch: use for QA

Each branch has its own connection string with slightly different host.

### Option B: Create Separate Databases

1. Neon Dashboard → SQL Editor
2. Connect to your project
3. Create new database:
   ```sql
   CREATE DATABASE surveycore_qa;
   CREATE DATABASE surveycore_prod;
   ```
4. Use connection strings:
   - QA: `postgresql://neondb_owner:password@host:5432/surveycore_qa?sslmode=require`
   - Production: `postgresql://neondb_owner:password@host:5432/surveycore_prod?sslmode=require`

## Configure Your .env Files

### Local Development (SQLite)
```bash
# .env
DATABASE_URL=sqlite:///./survey.db
```

### QA Deployment
```bash
# .env.qa (or create from .env.qa.example)
DATABASE_URL=postgresql://neondb_owner:your-password@your-host:5432/surveycore_qa?sslmode=require
```

### Production Deployment
```bash
# .env.production (or create from .env.production.example)
DATABASE_URL=postgresql://neondb_owner:your-password@your-host:5432/surveycore_prod?sslmode=require
```

## Database Initialization

The FastAPI app uses SQLAlchemy to auto-create tables on startup using:

```python
# surveycore_api/database.py
Base.metadata.create_all(bind=engine)
```

**First deployment workflow:**
1. Deploy code to Azure App Service
2. App starts → SQLAlchemy creates all tables automatically
3. API is ready

**To seed sample data:**
```bash
python init_db.py
```

## GitHub Secrets for Neon Credentials

Since the connection string contains a password, store it in GitHub Secrets:

### For surveycore-api repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**

**Secret 1: QA Database URL**
- Name: `NEON_DATABASE_URL_QA`
- Value: `postgresql://neondb_owner:password@host:5432/surveycore_qa?sslmode=require`
- Click **Add secret**

**Secret 2: Production Database URL**
- Name: `NEON_DATABASE_URL_PRODUCTION`
- Value: `postgresql://neondb_owner:password@host:5432/surveycore_prod?sslmode=require`
- Click **Add secret**

### Update .github/workflows/deploy.yml

Modify the workflow to inject Neon URLs into the environment files:

```yaml
deploy_qa:
  steps:
    - name: Create .env.qa with Neon credentials
      run: |
        cp .env.qa.example .env
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=${{ secrets.NEON_DATABASE_URL_QA }}|g" .env

deploy_production:
  steps:
    - name: Create .env.production with Neon credentials
      run: |
        cp .env.production.example .env
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=${{ secrets.NEON_DATABASE_URL_PRODUCTION }}|g" .env
```

## Migration from SQLite to PostgreSQL

If you have existing SQLite data and want to migrate:

### Option 1: Manual Export/Import

```bash
# Export SQLite to SQL
sqlite3 survey.db .dump > backup.sql

# Import into PostgreSQL (using psql)
psql -h your-neon-host -U neondb_owner -d surveycore_qa -f backup.sql
```

### Option 2: Using Python Script

```python
# migrate_db.py
from sqlalchemy import create_engine, inspect, text
import sqlite3

sqlite_engine = create_engine('sqlite:///./survey.db')
pg_engine = create_engine('postgresql://user:pass@host/db')

# Get all tables
inspector = inspect(sqlite_engine)
for table_name in inspector.get_table_names():
    # Read from SQLite
    df = pd.read_sql_table(table_name, sqlite_engine)
    # Write to PostgreSQL
    df.to_sql(table_name, pg_engine, if_exists='append', index=False)

print("Migration complete!")
```

## Monitoring & Backups

### Neon Console Features
- **Monitoring**: Dashboard shows connections, queries, storage
- **Backups**: Automatic daily backups (7-day retention on free tier)
- **Connection pooling**: Built-in to prevent connection exhaustion

### Restore from Backup
1. Neon Console → **Branches** → **Settings** → **Restore**
2. Select backup date
3. Click **Restore**

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `FATAL: invalid password` | Check Neon connection string for typos; regenerate password in console |
| `psycopg2.OperationalError: could not connect` | Verify host/port are correct; check network/firewall |
| `too many connections` | Increase connection pool limit in Neon settings or use connection pooling |
| `SSL verification failed` | Ensure `?sslmode=require` is in connection string |
| Slow queries | Check Neon Dashboard → Monitor → Slow queries |

## Cost Optimization

**Free tier includes:**
- 5 projects
- 1 database per project
- 0.5 GB storage
- Compute auto-suspend after 5 minutes inactivity

**For production, consider paid plan:**
- Dedicated compute (doesn't auto-suspend)
- More storage
- Premium support

## Environment Variables Summary

| Environment | Database | Connection String Location |
|-------------|----------|---------------------------|
| Local | SQLite | `.env` (DATABASE_URL=sqlite:///) |
| QA | PostgreSQL (Neon) | GitHub Secret `NEON_DATABASE_URL_QA` |
| Production | PostgreSQL (Neon) | GitHub Secret `NEON_DATABASE_URL_PRODUCTION` |

The API automatically creates all required tables on startup.
