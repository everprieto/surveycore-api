#!/bin/bash
# Azure App Service startup script
# Run from repo root: the surveycore_api/ package is resolved from here

pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations (if you add Alembic later)
# alembic upgrade head

gunicorn surveycore_api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
