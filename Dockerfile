# ============================================================
# Dockerfile — CRM System (Production)
# Base: python:3.11-slim
# WSGI: Gunicorn
# ============================================================

FROM python:3.12-slim

# ── Environment ──────────────────────────────────────────────
# Prevent .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Keep pip quiet and avoid root warnings
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ── Working directory ─────────────────────────────────────────
WORKDIR /app

# ── System dependencies ───────────────────────────────────────
# gcc          – needed to compile some Python C extensions
# libpq-dev    – PostgreSQL client headers (required by psycopg2)
# curl         – useful for health-check scripts
# netcat-traditional – used in entrypoint.sh to wait for the DB port
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        curl \
        netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────
# Copy only requirements first to leverage Docker layer caching:
# if requirements.txt hasn't changed, this layer is reused.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────
COPY . .

# ── Static files ──────────────────────────────────────────────
# Collect static assets so Nginx / WhiteNoise can serve them.
# DJANGO_SETTINGS_MODULE must point to a settings file that does
# NOT require a live database (production.py reads from env vars).
RUN DJANGO_SETTINGS_MODULE=crm.settings.production \
    SECRET_KEY=build-time-placeholder \
    DATABASE_URL=postgres://placeholder:placeholder@localhost:5432/placeholder \
    python manage.py collectstatic --noinput

# ── Non-root user ─────────────────────────────────────────────
# Running as a non-root user reduces the blast radius of any
# container escape or code-execution vulnerability.
RUN addgroup --system django && \
    adduser --system --ingroup django --no-create-home django && \
    # Give the django user ownership of the app directory so it
    # can write media uploads, logs, etc.
    chown -R django:django /app

USER django

# ── Network ───────────────────────────────────────────────────
EXPOSE 8000

# ── Entrypoint ────────────────────────────────────────────────
# entrypoint.sh waits for PostgreSQL, runs migrations, then
# executes the CMD (Gunicorn in production, runserver in dev).
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command: Gunicorn with 3 workers, 120-second timeout.
# Override this in docker-compose for development (runserver).
CMD ["gunicorn", "crm.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
