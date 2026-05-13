#!/bin/bash

# Entrypoint script for Django CRM application
# Waits for PostgreSQL, runs migrations, collects static files,
# optionally creates a superuser, then starts the application server.

set -e

# ─── Configuration ────────────────────────────────────────────────────────────
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
MAX_RETRIES=5
RETRY_INTERVAL=3

# ─── Helpers ──────────────────────────────────────────────────────────────────
log() {
    echo "[entrypoint] $(date '+%Y-%m-%d %H:%M:%S') $*"
}

# ─── Wait for PostgreSQL ───────────────────────────────────────────────────────
log "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."

attempt=1
while [ "$attempt" -le "$MAX_RETRIES" ]; do
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -q 2>/dev/null; then
        log "PostgreSQL is ready."
        break
    fi

    # Fallback to nc if pg_isready is not available
    if nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
        log "PostgreSQL is ready (via nc)."
        break
    fi

    log "Attempt ${attempt}/${MAX_RETRIES}: PostgreSQL not ready yet. Retrying in ${RETRY_INTERVAL}s..."
    sleep "$RETRY_INTERVAL"
    attempt=$((attempt + 1))
done

if [ "$attempt" -gt "$MAX_RETRIES" ]; then
    log "ERROR: PostgreSQL did not become ready after ${MAX_RETRIES} attempts. Exiting."
    exit 1
fi

# ─── Django Migrations ────────────────────────────────────────────────────────
log "Running database migrations..."
python manage.py migrate --noinput
log "Migrations complete."

# ─── Collect Static Files ─────────────────────────────────────────────────────
log "Collecting static files..."
python manage.py collectstatic --noinput
log "Static files collected."

# ─── Create Superuser (optional) ──────────────────────────────────────────────
# Set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, and
# DJANGO_SUPERUSER_PASSWORD in your environment to auto-create a superuser.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && \
   [ -n "$DJANGO_SUPERUSER_EMAIL" ] && \
   [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    log "Creating superuser '${DJANGO_SUPERUSER_USERNAME}' if not already present..."
    python manage.py createsuperuser \
        --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL" \
        2>/dev/null && log "Superuser created." || log "Superuser already exists, skipping."
else
    log "Superuser env vars not set — skipping superuser creation."
fi

# ─── Start Application Server ─────────────────────────────────────────────────
# In development (DJANGO_ENV=development) use Django's built-in runserver.
# In all other cases (production default) use Gunicorn.
if [ "${DJANGO_ENV:-production}" = "development" ]; then
    log "Starting Django development server on 0.0.0.0:8000..."
    exec python manage.py runserver 0.0.0.0:8000
else
    log "Starting Gunicorn on 0.0.0.0:8000 with 3 workers..."
    exec gunicorn crm.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 3 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile -
fi
