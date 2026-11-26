# Backend image (ADR0014). Build context is the REPO ROOT so task_resources/
# ships alongside the app and the seeder's relative path to seed.json resolves
# with no code change.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/backend

# Dependencies first for layer caching.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application code and the seed data, preserving the repo layout:
#   /app/backend/app/db/seed.py  ->  /app/task_resources/seed.json
COPY backend/ /app/backend/
COPY task_resources/ /app/task_resources/

RUN chmod +x /app/backend/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/backend/docker-entrypoint.sh"]
