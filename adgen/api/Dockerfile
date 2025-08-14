# syntax=docker/dockerfile:1.7
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip
RUN python -m venv /opt/venv
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM gcr.io/distroless/python3-debian12
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PYTHONPATH=/opt/venv/lib/python3.11/site-packages
COPY main.py settings.py orchestrator.py ./
EXPOSE 8000
CMD ["/usr/bin/python3.11", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
