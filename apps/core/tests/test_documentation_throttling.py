"""Documentation must remain accessible when an API-data quota is exhausted."""

from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import resolve, reverse

from apps.core.permissions import CachedHasAPIKey
from apps.core.throttles import PerAPIKeyRateThrottle


class DocumentationThrottleTests(SimpleTestCase):
    def test_documentation_bypasses_exhausted_api_data_throttle(self):
        with patch.object(PerAPIKeyRateThrottle, 'allow_request', return_value=False) as throttle:
            for route in ('swagger-ui', 'redoc', 'schema'):
                with self.subTest(route=route):
                    url = reverse(route)
                    view = resolve(url)
                    self.assertEqual(view.func.view_initkwargs['throttle_classes'], [])
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
            throttle.assert_not_called()

    def test_api_data_still_enforces_exhausted_quota(self):
        # Bypass only authentication, so the request reaches the real throttle
        # without needing a database or a real API key.
        with (
            patch.object(CachedHasAPIKey, 'has_permission', return_value=True),
            patch.object(PerAPIKeyRateThrottle, 'allow_request', return_value=False) as throttle,
        ):
            response = self.client.get(reverse('book-list'))
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response)
        throttle.assert_called_once()
