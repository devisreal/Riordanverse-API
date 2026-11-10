from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='pj_fandom_dev'),
        'USER': env('DB_USER', default='pj_fandom_user'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Development helpers belong here, independent of the .env DEBUG value.
# Copy the base lists so importing development settings does not mutate them.
INSTALLED_APPS = [*INSTALLED_APPS, 'django_extensions']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Fine for local dev only — never enable this in production
CORS_ALLOW_ALL_ORIGINS = True

# Keep API-key requirements and request/security logging in development too.
LOGGING['root']['level'] = 'INFO'
LOGGING['loggers']['django']['level'] = 'INFO'
LOGGING['handlers']['console']['formatter'] = 'color_json'
