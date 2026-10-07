# Ember API container. Build context is the REPO ROOT (the API imports the
# top-level `search_engine` package):
#   docker build -f backend/Dockerfile -t ember-api .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY search_engine ./search_engine
COPY backend ./backend

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 ember && chown -R ember /app
USER ember

EXPOSE 8000

# Apply database migrations, then serve. $PORT is provided by Render/Cloud Run/Fly.
CMD ["sh", "-c", "python -m alembic -c backend/alembic.ini upgrade head && exec python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
