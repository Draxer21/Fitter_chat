FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Install rasa-sdk and action dependencies
COPY requirements-actions.txt .
RUN pip install --no-cache-dir -r requirements-actions.txt

# Copy both actions and backend (actions imports backend.planner.* and backend.food.*)
COPY actions/ actions/
COPY backend/ backend/

EXPOSE 5055

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5055/health || exit 1

CMD ["python", "-m", "rasa_sdk", "--actions", "actions", "--port", "5055"]
