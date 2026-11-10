# ─── Stage 1: Builder (Air-Gapped / Offline via pre-fetched wheels) ───
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy official uv binary from pre-pulled image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN uv venv /opt/venv

ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH

COPY pyproject.toml README.md ./
COPY src ./src
COPY wheels* ./wheels_opt/

# Install packages: uses offline wheels if present, falls back to PyPI
RUN if [ -d "./wheels_opt" ] && [ -n "$(ls -A ./wheels_opt 2>/dev/null)" ]; then \
        echo "Building offline using pre-fetched wheels..." && \
        uv pip install --no-index --find-links=wheels_opt . psycopg-binary; \
    else \
        echo "Building online from PyPI..." && \
        uv pip install . "psycopg[binary]>=3.2.0"; \
    fi

# ─── Stage 2: Minimal Runtime ───
FROM python:3.12-slim AS runtime

WORKDIR /app

# Run as non-privileged system user (Slide 40 & 41)
RUN groupadd -r app && \
    useradd -r -g app -d /app app && \
    chown -R app:app /app

# Copy virtualenv from builder stage
COPY --from=builder --chown=app:app /opt/venv /opt/venv

# Copy runtime assets and specs required by Connexion and Alembic
COPY --chown=app:app openapi ./openapi
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app wsgi.py gunicorn.conf.py ./
COPY --chown=app:app src ./src

ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    OPENAPI_SPEC_DIR=/app/openapi \
    FLASK_APP=wsgi:flask_app

USER app

EXPOSE 5000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "gunicorn.conf.py", "wsgi:app"]
