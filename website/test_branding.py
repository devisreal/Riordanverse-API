"""Branding changes must not hard-code deployment hosts into local routes."""

import json
import os
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase

from website.content import GITHUB_URL, LORE_CORRECTION_URL


class BrandingTests(SimpleTestCase):
    def test_project_and_repository_identity(self):
        self.assertEqual(settings.SPECTACULAR_SETTINGS['TITLE'], 'Riordanverse API')
        self.assertEqual(GITHUB_URL, 'https://github.com/devisreal/Riordanverse-API')
        self.assertEqual(
            LORE_CORRECTION_URL, f'{GITHUB_URL}/issues/new?template=lore_correction.yml'
        )
        response = self.client.get('/')
        self.assertContains(response, 'aria-label="Riordanverse API home"')
        self.assertContains(response, 'Current coverage focuses on Percy Jackson')
        self.assertContains(response, 'http://testserver/api/v1/')
        self.assertNotContains(response, 'Percy Jackson Fandom API')

    def test_default_application_sender_identities(self):
        code = (
            'import json, environ; '
            'environ.Env.read_env = lambda *args, **kwargs: None; '
            'from config.settings import base; '
            'print(json.dumps([base.DEFAULT_FROM_EMAIL, base.SERVER_EMAIL]))'
        )
        environment = {
            **os.environ,
            'SECRET_KEY': 'test-only-secret',
            'DEBUG': 'False',
            'ALLOWED_HOSTS': 'localhost',
            'CORS_ALLOWED_ORIGINS': '',
            'REDIS_URL': 'redis://localhost:6379/1',
        }
        environment.pop('DEFAULT_FROM_EMAIL', None)
        environment.pop('SERVER_EMAIL', None)
        for overrides, expected in (
            ({}, ['Riordanverse API <support@riordanverse.cc>', 'support@riordanverse.cc']),
            (
                {
                    'DEFAULT_FROM_EMAIL': 'Custom <sender@example.org>',
                    'SERVER_EMAIL': 'ops@example.org',
                },
                ['Custom <sender@example.org>', 'ops@example.org'],
            ),
        ):
            with self.subTest(overrides=overrides):
                result = subprocess.run(
                    [sys.executable, '-c', code],
                    env={**environment, **overrides},
                    cwd=settings.BASE_DIR,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(json.loads(result.stdout), expected)
