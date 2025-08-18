FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# If you have requirements.txt, keep this block
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt
# If you don't have requirements.txt, at least ensure deps:
# RUN pip install --upgrade pip && pip install fastapi "uvicorn[standard]"

COPY . /app

EXPOSE 8080
CMD ["python","server.py"]
