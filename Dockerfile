# ─────────────────────────────────────────────────────────────
# Stage 1: Build — install dependencies into virtual prefix
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─────────────────────────────────────────────────────────────
# Stage 2: Runtime — minimal production image
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Create dedicated non-root application user
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Ensure appuser owns application directory
RUN mkdir -p logs && chown -R appuser:appgroup /app

USER appuser

# Default production environment settings
ENV PORT=5000
ENV WORKERS=2
ENV TIMEOUT=60
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT}/api/health')" || exit 1

# Production Gunicorn WSGI command with graceful SIGTERM termination
CMD ["sh", "-c", "exec gunicorn wsgi:app \
    --bind 0.0.0.0:${PORT} \
    --workers ${WORKERS} \
    --timeout ${TIMEOUT} \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --forwarded-allow-ips='*'"]
