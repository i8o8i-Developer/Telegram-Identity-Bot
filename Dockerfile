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

# ================================
# Stage 2 - Production Image
# ================================
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=builder /wheels /wheels
COPY Requirements.txt .

RUN pip install --no-cache-dir --no-index --find-links /wheels -r Requirements.txt \
    && rm -rf /wheels Requirements.txt

COPY . .

RUN mkdir -p /app/logs && chmod 755 /app/logs

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    PORT=3000 \
    LOG_LEVEL=INFO \
    WEBHOOK_URL=https://bot.durgaaisolutions.in

RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://127.0.0.1:3000/healthz || exit 1

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:3000", "--timeout", "120", "--keep-alive", "5", "Main:app"]
