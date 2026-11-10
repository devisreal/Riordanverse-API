"""Production integration checks without database access or a running server."""

import json
import os
import runpy
import subprocess
import sys
from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase

PRODUCTION_PROBE = """
import json
from config.settings import base
base_middleware = list(base.MIDDLEWARE)
from config.settings import production
from django.core.wsgi import get_wsgi_application
from django.core.files.storage import storages
from django.test import Client

application = get_wsgi_application()
redirect = Client().get('/static/css/dist/styles.css')
print(json.dumps({
    'debug': production.DEBUG,
    'middleware': production.MIDDLEWARE,
    'base_before': base_middleware,
    'base_after': base.MIDDLEWARE,
    'static_storage': production.STORAGES['staticfiles']['BACKEND'],
    'default_storage': type(storages['default']).__name__,
    'application': type(application).__name__,
    'http_static_status': redirect.status_code,
    'http_static_redirect': redirect.headers.get('Location'),
}))
"""


class DeploymentTests(SimpleTestCase):
    def production_environment(self):
        return {
            **os.environ,
            'DJANGO_SETTINGS_MODULE': 'config.settings.production',
            'DEBUG': 'False',
            'SECRET_KEY': 'deployment-test-placeholder-not-a-real-secret',
            'ALLOWED_HOSTS': 'localhost,127.0.0.1,testserver',
            'DB_NAME': 'deployment_test',
            'DB_USER': 'deployment_test',
            'DB_PASSWORD': 'not-used',
            'DB_HOST': '127.0.0.1',
            'DB_PORT': '1',
            'REDIS_URL': 'redis://127.0.0.1:1/0',
            'CORS_ALLOWED_ORIGINS': '',
        }

    def run_probe(self, arguments):
        result = subprocess.run(
            [sys.executable, *arguments],
            env=self.production_environment(),
            check=False,
            cwd=settings.BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_production_wsgi_boots_with_whitenoise_and_preserves_base_settings(self):
        snapshot = json.loads(self.run_probe(['-c', PRODUCTION_PROBE]).stdout)
        self.assertFalse(snapshot['debug'])
        self.assertEqual(snapshot['application'], 'WSGIHandler')
        middleware = snapshot['middleware']
        security_index = middleware.index('django.middleware.security.SecurityMiddleware')
        self.assertEqual(
            middleware[security_index + 1], 'whitenoise.middleware.WhiteNoiseMiddleware'
        )
        self.assertEqual(middleware.count('whitenoise.middleware.WhiteNoiseMiddleware'), 1)
        self.assertEqual(snapshot['base_before'], snapshot['base_after'])
        self.assertNotIn('whitenoise.middleware.WhiteNoiseMiddleware', snapshot['base_after'])
        self.assertEqual(
            snapshot['static_storage'],
            'whitenoise.storage.CompressedManifestStaticFilesStorage',
        )
        self.assertEqual(snapshot['default_storage'], 'FileSystemStorage')
        self.assertEqual(snapshot['http_static_status'], 301)
        self.assertEqual(
            snapshot['http_static_redirect'], 'https://testserver/static/css/dist/styles.css'
        )

    def test_gunicorn_defaults(self):
        with patch.dict(os.environ):
            os.environ.pop('PORT', None)
            os.environ.pop('WEB_CONCURRENCY', None)
            config = runpy.run_path(str(settings.BASE_DIR / 'gunicorn.conf.py'))
        self.assertEqual(config['wsgi_app'], 'config.wsgi:application')
        self.assertEqual(config['bind'], '0.0.0.0:8000')
        self.assertEqual(config['workers'], 1)
        self.assertIsNone(config['accesslog'])
        self.assertEqual(config['errorlog'], '-')

    def test_gunicorn_accepts_host_port_and_worker_count(self):
        with patch.dict(os.environ, PORT='9123', WEB_CONCURRENCY='2'):
            config = runpy.run_path(str(settings.BASE_DIR / 'gunicorn.conf.py'))
        self.assertEqual(config['bind'], '0.0.0.0:9123')
        self.assertEqual(config['workers'], 2)

    def test_gunicorn_can_load_the_production_wsgi_application(self):
        self.run_probe(['-m', 'gunicorn', '--check-config', '--config', 'gunicorn.conf.py'])
