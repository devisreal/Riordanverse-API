from pathlib import Path

import environ

# ---------------------------------------------------------------------------
# * Paths & environment loading
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')
APP_VERSION = env('APP_VERSION', default='0.1.0')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# * Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'django_filters',
    'rest_framework_api_key',
    'drf_spectacular',
    'watson',
    'corsheaders',
]

LOCAL_APPS = [
    'apps.core',
    'apps.images',
    'apps.characters',
    'apps.divinities',
    'apps.bestiary',
    'apps.items',
    'apps.locations',
    'apps.narrative',
    'apps.organizations',
    'apps.search',
    'apps.access',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {'()': 'apps.core.logging.JsonEventFormatter'},
        'color_json': {'()': 'apps.core.logging.ColorJsonEventFormatter'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'json'},
    },
    'root': {'handlers': ['console'], 'level': 'WARNING'},
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'api.request': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'api.security': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}


# ---------------------------------------------------------------------------
# * Middleware
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    'apps.core.middleware.RequestLoggingMiddleware',
    'apps.core.middleware.RateLimitHeadersMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ---------------------------------------------------------------------------
# * Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# * Static files (admin assets + drf-spectacular Swagger UI)
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ---------------------------------------------------------------------------
# * Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    # Secure by default: every request needs a valid API key.
    # CachedHasAPIKey wraps rest_framework_api_key's HasAPIKey with a
    # Redis-backed lookup so we don't hit Postgres on every request.
    'DEFAULT_PERMISSION_CLASSES': [
        'apps.core.permissions.CachedHasAPIKey',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'apps.core.filters.SortOrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.EnvelopePagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'apps.core.schema.APIKeyAutoSchema',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_THROTTLE_CLASSES': [
        'apps.core.throttles.PerAPIKeyRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'api_key': '1000/hour',
        'anon': '100/day',
        'user': '1000/day',
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Percy Jackson Fandom API',
    'DESCRIPTION': (
        'A read-only REST API for the Riordanverse. Protected endpoints require an X-API-Key '
        'header; public health and API-key management routes are explicitly marked in the schema.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': [],
    'ENUM_NAME_OVERRIDES': {
        'CharacterStatusEnum': 'apps.core.choices.STATUS_CHOICES',
        'HealthStatusEnum': 'apps.core.schema_serializers.HEALTH_STATUS_CHOICES',
        'TitanAlignmentEnum': 'apps.core.choices.TITAN_ALIGNMENT_CHOICES',
        'CreatureAlignmentEnum': 'apps.bestiary.models.CREATURE_ALIGNMENT_CHOICES',
        'FactionAlignmentEnum': 'apps.organizations.models.FACTION_ALIGNMENT_CHOICES',
    },
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'ApiKeyAuth': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API-Key',
                'description': 'Consumer API key. Request one at POST /auth/request-key/.',
            },
        },
    },
}

# ---------------------------------------------------------------------------
# * API key header + Redis cache (used by CachedHasAPIKey)
# ---------------------------------------------------------------------------
API_KEY_CUSTOM_HEADER = env('API_KEY_CUSTOM_HEADER', default='HTTP_X_API_KEY')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}

# ---------------------------------------------------------------------------
# * CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')
CORS_EXPOSE_HEADERS = [
    'RateLimit-Limit',
    'RateLimit-Remaining',
    'RateLimit-Reset',
    'Retry-After',
]

# ---------------------------------------------------------------------------
# * django-watson (search)
# ---------------------------------------------------------------------------
WATSON_ITERATOR_CHUNK_SIZE = 2000
