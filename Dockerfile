# Multi-stage Build For Production Optimization
FROM python:3.11-slim as builder

# Install Build Dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create Wheel Packages
WORKDIR /wheels
COPY Requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r Requirements.txt

# Production Stage
FROM python:3.11-slim

# Create Non-Root User for Security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install Runtime Dependencies Only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set Working Directory
WORKDIR /app

# Production Environment Variables
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=3000

# Copy Wheels And Install
COPY --from=builder /wheels /wheels
COPY Requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links /wheels -r Requirements.txt \
    && rm -rf /wheels Requirements.txt

# Copy Application Code
COPY --chown=appuser:appuser . .

# Create Logs Directory
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Switch To Non-Root User
USER appuser

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/healthz || exit 1

# Expose Port 3000 For Coolify
EXPOSE 3000

# Use Gunicorn For Production With Proper Worker Management
CMD ["gunicorn", "Main:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:3000", "--timeout", "120", "--keep-alive", "2", \
     "--max-requests", "1000", "--max-requests-jitter", "100", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "--log-level", "info"]
