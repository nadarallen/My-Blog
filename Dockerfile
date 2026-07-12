# ─────────────────────────────────────────────
# Stage 1: Build — install dependencies
# ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─────────────────────────────────────────────
# Stage 2: Runtime — minimal production image
# ─────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Create uploads directory and give ownership to appuser
RUN mkdir -p static/uploads && chown -R appuser:appuser /app

USER appuser

# Gunicorn settings
ENV PORT=5000
ENV WORKERS=4
ENV TIMEOUT=120

EXPOSE 5000

# Production: Gunicorn with 4 async workers
CMD ["sh", "-c", "gunicorn wsgi:app \
    --bind 0.0.0.0:${PORT} \
    --workers ${WORKERS} \
    --timeout ${TIMEOUT} \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --forwarded-allow-ips='*' \
    --proxy-protocol"]
