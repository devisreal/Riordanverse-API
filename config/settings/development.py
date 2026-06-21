from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="pj_fandom_dev"),
        "USER": env("DB_USER", default="pj_fandom_user"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    }
}

# Handy for `manage.py shell_plus`, etc. — optional, dev-only dependency
INSTALLED_APPS += ["django_extensions"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Fine for local dev only — never enable this in production
CORS_ALLOW_ALL_ORIGINS = True

# Loosen auth locally so you can browse the API / Swagger UI without
# generating a key every time. Production keeps base.py's strict default.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}