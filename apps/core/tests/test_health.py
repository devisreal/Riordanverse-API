from unittest.mock import MagicMock, patch

from django.conf import settings
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class HealthEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_liveness_is_public_and_does_not_check_database(self):
        with patch('apps.core.views.connections') as connections:
            response = self.client.get(reverse('health-live'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['version'], settings.APP_VERSION)
        self.assertEqual(response['Cache-Control'], 'no-store, max-age=0')
        connections.__getitem__.assert_not_called()

    def test_readiness_is_public_and_checks_database(self):
        response = self.client.get(reverse('health-ready'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['checks']['database'], 'connected')

    def test_readiness_returns_503_without_leaking_database_error(self):
        with patch('apps.core.views.connections') as connections:
            cursor_context = MagicMock()
            cursor_context.__enter__.side_effect = DatabaseError('private connection details')
            connections.__getitem__.return_value.cursor.return_value = cursor_context

            response = self.client.get(reverse('health-ready'))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data['status'], 'not_ready')
        self.assertEqual(response.data['checks']['database'], 'unavailable')
        self.assertNotIn('private connection details', response.content.decode())
