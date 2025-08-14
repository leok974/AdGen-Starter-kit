# syntax=docker/dockerfile:1.7

# Builder (Google mirror to avoid Docker Hub)
FROM mirror.gcr.io/library/python:3.11-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m venv /opt/venv && . /opt/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# Runtime (distroless python)
FROM gcr.io/distroless/python3-debian12
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:${PATH}"
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY main.py settings.py orchestrator.py ./
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
