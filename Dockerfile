# =========================
# Stage 1: frontend builder
# Builds the admin SPA (frontend/) into skill_hub/static/admin.
# =========================
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Install pnpm (matches the committed pnpm-lock.yaml major version)
RUN npm install -g pnpm@10

# Install dependencies first (better layer caching: only re-runs when manifests change)
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copy the rest of the frontend source and build.
# vite.config.ts outputs to ../skill_hub/static/admin → /app/skill_hub/static/admin
COPY frontend/ ./
RUN pnpm build


# =========================
# Stage 2: python builder
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
# Stage 3: runtime
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

# Copy application source (skill_hub/static/admin is .dockerignored, so the
# admin bundle comes solely from the frontend-builder stage below)
COPY --chown=skillhub:skillhub . /app

# Copy the freshly built admin SPA from the frontend stage
COPY --from=frontend-builder --chown=skillhub:skillhub \
    /app/skill_hub/static/admin /app/skill_hub/static/admin

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
