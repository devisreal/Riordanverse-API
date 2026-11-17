"""Production settings for local Docker Compose over HTTP."""

from .production import *

# Local Docker is not the public production origin.
SEO_PUBLIC_ORIGIN = env('SEO_PUBLIC_ORIGIN', default='')
SEO_INDEXING_ENABLED = env.bool('SEO_INDEXING_ENABLED', default=False)

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_PROXY_SSL_HEADER = None
