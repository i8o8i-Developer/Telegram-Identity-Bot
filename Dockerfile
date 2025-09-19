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

EXPOSE 3000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:3000", "Main:app"]
