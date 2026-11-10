"""Load settings in fresh interpreters to exercise import order and .env overrides."""

import json
import os
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase

RELOAD_APP = 'django_browser_reload'
RELOAD_MIDDLEWARE = 'django_browser_reload.middleware.BrowserReloadMiddleware'

SETTINGS_PROBE = """
import json
import os
from importlib import import_module

import django
from django.urls import Resolver404, resolve

module = os.environ['DJANGO_SETTINGS_MODULE']
selected = import_module(module)
reload_view = None
if module != 'config.settings.base':
    django.setup()
    try:
        reload_view = resolve('/__reload__/events/').view_name
    except Resolver404:
        pass
base = import_module('config.settings.base')
print(json.dumps({
    'debug': selected.DEBUG,
    'apps': selected.INSTALLED_APPS,
    'middleware': selected.MIDDLEWARE,
    'base_apps': base.INSTALLED_APPS,
    'base_middleware': base.MIDDLEWARE,
    'reload_view': reload_view,
}))
"""


class BrowserReloadSettingsTests(SimpleTestCase):
    def snapshot(self, module, debug):
        environment = {
            **os.environ,
            'DJANGO_SETTINGS_MODULE': f'config.settings.{module}',
            'DEBUG': str(debug),
            'SECRET_KEY': 'settings-test-placeholder',
            'ALLOWED_HOSTS': 'localhost,127.0.0.1,testserver',
            'DB_NAME': 'settings_test',
            'DB_USER': 'settings_test',
            'DB_PASSWORD': 'not-used',
            'DB_HOST': '127.0.0.1',
            'DB_PORT': '1',
            'REDIS_URL': 'redis://127.0.0.1:1/0',
            'CORS_ALLOWED_ORIGINS': 'http://localhost:3000',
        }
        result = subprocess.run(
            [sys.executable, '-c', SETTINGS_PROBE],
            env=environment,
            cwd=settings.BASE_DIR,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_base_and_test_settings_do_not_register_reload(self):
        for module in ('base', 'test'):
            for debug in (False, True):
                with self.subTest(module=module, environment_debug=debug):
                    snapshot = self.snapshot(module, debug)
                    self.assertNotIn(RELOAD_APP, snapshot['apps'])
                    self.assertNotIn(RELOAD_MIDDLEWARE, snapshot['middleware'])
                    if module == 'test':
                        self.assertFalse(snapshot['debug'])
                        self.assertIsNone(snapshot['reload_view'])

    def test_development_enables_reload_regardless_of_environment_debug(self):
        for debug in (False, True):
            with self.subTest(environment_debug=debug):
                snapshot = self.snapshot('development', debug)
                self.assertTrue(snapshot['debug'])
                self.assertEqual(snapshot['apps'].count(RELOAD_APP), 1)
                self.assertEqual(snapshot['middleware'].count(RELOAD_MIDDLEWARE), 1)
                self.assertEqual(snapshot['reload_view'], 'django_browser_reload:events')
                self.assertNotIn(RELOAD_APP, snapshot['base_apps'])
                self.assertNotIn('django_extensions', snapshot['base_apps'])
                self.assertNotIn(RELOAD_MIDDLEWARE, snapshot['base_middleware'])

    def test_production_excludes_reload_regardless_of_environment_debug(self):
        for debug in (False, True):
            with self.subTest(environment_debug=debug):
                snapshot = self.snapshot('production', debug)
                self.assertFalse(snapshot['debug'])
                self.assertNotIn(RELOAD_APP, snapshot['apps'])
                self.assertNotIn(RELOAD_MIDDLEWARE, snapshot['middleware'])
                self.assertIsNone(snapshot['reload_view'])
