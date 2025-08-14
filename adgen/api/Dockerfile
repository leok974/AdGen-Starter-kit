# syntax=docker/dockerfile:1.7

# ---- Builder (no Docker Hub) ----
FROM mirror.gcr.io/library/python:3.11-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m venv /opt/venv && . /opt/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# ---- Runtime (distroless python) ----
FROM gcr.io/distroless/python3-debian12
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
# Make sure uvicorn/python from the venv are first on PATH
ENV PATH="/opt/venv/bin:${PATH}"
# Copy only the sources we need
COPY main.py settings.py orchestrator.py server.py ./
EXPOSE 8000
# Use the venv's uvicorn directly
CMD ["python3", "server.py"]
