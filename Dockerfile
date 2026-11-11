# syntax=docker/dockerfile:1

ARG PYTHON_IMAGE=python:3.14-slim-bookworm

# ------------------------------------------------------------
# 1. Build frontend assets
# ------------------------------------------------------------
FROM node:22-bookworm-slim AS frontend

WORKDIR /app/website/static_src

# Cache npm dependencies separately from application source.
COPY website/static_src/package.json website/static_src/package-lock.json ./

RUN npm ci

# Tailwind scans the Django templates and application source.
WORKDIR /app
COPY . .

RUN npm run build --prefix website/static_src


# ------------------------------------------------------------
# 2. Install Python dependencies and collect static assets
# ------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS build

COPY --from=ghcr.io/astral-sh/uv:0.12.5 \
  /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  UV_PYTHON_DOWNLOADS=never \
  UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1 \
  UV_PROJECT_ENVIRONMENT=/opt/venv \
  PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Cache locked Python dependencies separately from source changes.
COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev --no-install-project

COPY . .

# Generated assets are excluded from the host build context.
# Copy the versions built in the frontend stage instead.
COPY --from=frontend \
  /app/website/static/css/dist/ \
  ./website/static/css/dist/

COPY --from=frontend \
  /app/website/static/website/js/dist/ \
  ./website/static/website/js/dist/

COPY --from=frontend \
  /app/website/static/vendor/swagger-ui/dist/ \
  ./website/static/vendor/swagger-ui/dist/

# These are build-only placeholders, not deployment credentials.
# collectstatic loads Django settings but does not need a live database.
RUN DJANGO_SETTINGS_MODULE=config.settings.production \
  SECRET_KEY=build-only-placeholder-not-a-production-secret \
  DEBUG=False \
  ALLOWED_HOSTS=localhost \
  DB_NAME=build_placeholder \
  DB_USER=build_placeholder \
  DB_PASSWORD=build_placeholder \
  DB_HOST=127.0.0.1 \
  DB_PORT=5432 \
  REDIS_URL=redis://127.0.0.1:6379/0 \
  CORS_ALLOWED_ORIGINS="" \
  python manage.py collectstatic --noinput

# Frontend build tooling is not needed by the running application.
RUN rm -rf website/static_src website/tests_js


# ------------------------------------------------------------
# 3. Production runtime
# ------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS runtime

ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  DJANGO_SETTINGS_MODULE=config.settings.production \
  PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN groupadd --gid 10001 app \
  && useradd \
  --uid 10001 \
  --gid app \
  --create-home \
  --shell /usr/sbin/nologin \
  app

COPY --from=build /opt/venv /opt/venv

COPY --from=build /app/apps ./apps
COPY --from=build /app/config ./config
COPY --from=build /app/website ./website
COPY --from=build /app/data ./data
COPY --from=build /app/staticfiles ./staticfiles
COPY --from=build /app/manage.py /app/gunicorn.conf.py ./

USER app

EXPOSE 8000

CMD ["gunicorn", "--config", "gunicorn.conf.py"]
