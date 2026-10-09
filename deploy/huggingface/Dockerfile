# Ember API on a Hugging Face Docker Space (free, no card).
# This file is copied to the ROOT of the Space repo next to backend/ and search_engine/
# by deploy/huggingface/publish.sh.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY search_engine ./search_engine
COPY backend ./backend

# Spaces run the container as uid 1000.
RUN useradd --create-home --uid 1000 user && chown -R user /app
USER user

EXPOSE 7860
CMD ["sh", "-c", "python -m alembic -c backend/alembic.ini upgrade head && exec python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-7860}"]
