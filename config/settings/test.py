from .base import *  # noqa: F401,F403

DEBUG = False
SECRET_KEY = "test-secret-key-not-for-production"

# SQLite avoids PostgreSQL session/connection conflicts during test runs
# (per your existing guidelines doc).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

# Faster password hashing — tests don't need real security
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Local-memory cache instead of Redis — no Redis dependency needed to run tests
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

# Don't require an API key for test client requests by default
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"