# syntax=docker/dockerfile:1.6

# =========================
# Stage 1: builder
# =========================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies (needed for some Python packages that may compile from source)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into an isolated prefix for copy into the final image
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt


# =========================
# Stage 2: runtime
# =========================
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SKILL_HUB_HOST=0.0.0.0 \
    SKILL_HUB_PORT=8080 \
    SKILL_HUB_DATA_DIR=/app/data \
    SKILL_HUB_LOG_LEVEL=INFO \
    SKILL_HUB_API_PREFIX=/api

# Install runtime system dependencies (libpq for psycopg2, curl for healthcheck)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user to run the application
RUN groupadd --system --gid 1000 skillhub \
    && useradd --system --uid 1000 --gid skillhub --create-home --shell /bin/bash skillhub

WORKDIR /app

# Copy installed Python dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=skillhub:skillhub . /app

# Ensure the data directory exists and is writable
RUN mkdir -p /app/data \
    && chown -R skillhub:skillhub /app \
    && chmod +x /app/start_server.sh

USER skillhub

EXPOSE 8080

# Basic healthcheck hitting the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${SKILL_HUB_PORT:-8080}/health" || exit 1

# Use tini as PID 1 for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--", "/app/start_server.sh"]
