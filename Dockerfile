# ================================
# Stage 1 - Build Dependencies
# ================================
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make curl \
    && rm -rf /var/lib/apt/lists/*

COPY Requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r Requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
COPY Requirements.txt .

RUN pip install --no-cache-dir --no-index --find-links /wheels -r Requirements.txt \
    && rm -rf /wheels

COPY . .

ENV PYTHONUNBUFFERED=1 \
    APP_ENV=production

ENV PORT=3000 \
    LOG_LEVEL=INFO

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://127.0.0.1:3000/healthz || exit 1

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:3000", "Main:app"]
