FROM python:3.11-slim

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY Requirements.txt .
RUN pip install -r Requirements.txt

COPY . .

CMD ["sh", "-c", "uvicorn Main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]