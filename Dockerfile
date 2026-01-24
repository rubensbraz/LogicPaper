# ==========================================
# STAGE 1: Base (Runtime Environment)
# ==========================================
FROM python:3.11-alpine AS base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    PYTHONUSERBASE=/home/logicuser/.local

# Add the local bin directory to PATH
ENV PATH=/home/logicuser/.local/bin:$PATH

WORKDIR $APP_HOME

# Install essential runtime dependencies:
# - libreoffice & openjdk11-jre: Core engine for Office-to-PDF conversion
# - fonts: Critical for correct character rendering in documents (Boolean/Mask strategies)
# - tzdata: Required for date arithmetic in DateStrategy
# - curl: Required for container health checks
# - shadow: Required for secure user management
RUN apk add --no-cache \
    libreoffice \
    openjdk11-jre \
    font-noto \
    ttf-dejavu \
    ttf-liberation \
    ttf-freefont \
    tzdata \
    curl \
    shadow \
    libxml2 \
    libxslt \
    jpeg \
    zlib

# ==========================================
# STAGE 2: Builder (Compile Dependencies)
# ==========================================
FROM base AS builder

# Install build-time dependencies (compilers) to install Python extensions (Pillow, Pandas, etc)
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    libffi-dev \
    musl-dev \
    jpeg-dev \
    zlib-dev \
    libxml2-dev \
    libxslt-dev

RUN pip install --no-cache-dir --upgrade pip

# Copy and install requirements into a local user directory for easy transfer
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# STAGE 3: Production (Final Image)
# ==========================================
FROM base AS production

# Security: Create a non-root user to run the application
RUN useradd -m logicuser && \
    mkdir -p /data/temp /app/persistent_templates && \
    chown -R logicuser:logicuser /app /data

# Copy compiled Python packages from the builder stage
COPY --from=builder --chown=logicuser:logicuser /home/logicuser/.local /home/logicuser/.local

# Copy application source code
COPY --chown=logicuser:logicuser . .

# Switch to the non-root user
USER logicuser

# Expose FastAPI default port
EXPOSE 8000

# Healthcheck to ensure FastAPI and LibreOffice are responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start the application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]