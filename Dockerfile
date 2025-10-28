# ==========================================
# Multi-stage Dockerfile for RAG Pipeline
# ==========================================
# Production-ready Docker image with:
# - Multi-stage build for smaller image size
# - Non-root user for security
# - Optimized layer caching
# - Gunicorn + Uvicorn for production serving
# ==========================================

# ==========================================
# Stage 1: Builder
# ==========================================
# This stage compiles and installs all dependencies
FROM python:3.10-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /build

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip, setuptools, and wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy only requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies to user directory
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Runtime
# ==========================================
# This stage contains only what's needed to run the application
FROM python:3.10-slim

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive
ARG APP_VERSION=1.0.0

# Labels for container metadata
LABEL maintainer="RAG Pipeline Team"
LABEL version="${APP_VERSION}"
LABEL description="Production-ready RAG Pipeline API"

# Set working directory
WORKDIR /app

# Install only runtime dependencies (smaller image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user with specific UID for consistency
RUN groupadd -r -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -m -s /bin/bash appuser && \
    mkdir -p /app/uploads /app/logs /app/temp && \
    chown -R appuser:appuser /app

# Copy Python dependencies from builder stage
#COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy Gunicorn configuration
COPY --chown=appuser:appuser gunicorn_conf.py .

# Copy application code (excluding files in .dockerignore)
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini .

# Switch to non-root user
USER appuser

# Add local pip binaries to PATH
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Expose application port
EXPOSE 8000

# Enhanced health check with proper error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - can be overridden in docker-compose
# Production: Uses Gunicorn with Uvicorn workers
# Development: Override with --reload flag
CMD ["gunicorn", "app.main:app", "-c", "gunicorn_conf.py"]

