"""Browser clients get explicit-origin CORS, never an authentication bypass."""

from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from django.urls import resolve, reverse

from apps.core.permissions import CachedHasAPIKey
from apps.core.throttles import PerAPIKeyRateThrottle


@override_settings(CORS_ALLOWED_ORIGINS=['https://frontend.example'])
class BrowserCORSTests(SimpleTestCase):
    origin = 'https://frontend.example'

    def preflight(self, origin):
        return self.client.options(
            reverse('book-list'),
            HTTP_ORIGIN=origin,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='x-api-key',
        )

    def test_preflight_allows_key_header_without_auth_or_quota(self):
        with (
            patch.object(CachedHasAPIKey, 'has_permission') as permission,
            patch.object(PerAPIKeyRateThrottle, 'allow_request') as throttle,
        ):
            response = self.preflight(self.origin)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Access-Control-Allow-Origin'], self.origin)
        self.assertIn('x-api-key', response['Access-Control-Allow-Headers'].lower())
        self.assertIn('GET', response['Access-Control-Allow-Methods'])
        self.assertNotIn('Access-Control-Allow-Credentials', response)
        permission.assert_not_called()
        throttle.assert_not_called()

    def test_unapproved_origins_are_not_allowed(self):
        for origin in ('https://other.example', 'https://frontend.example.evil', 'null'):
            with self.subTest(origin=origin):
                self.assertNotIn('Access-Control-Allow-Origin', self.preflight(origin))

    @override_settings(CORS_ALLOWED_ORIGINS=[])
    def test_empty_allowlist_disables_cross_origin_access(self):
        self.assertNotIn('Access-Control-Allow-Origin', self.preflight(self.origin))

    def test_directory_response_exposes_quota_headers_without_credentials(self):
        response = self.client.get('/api/v1/', HTTP_ORIGIN=self.origin)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Access-Control-Allow-Origin'], self.origin)
        exposed = response['Access-Control-Expose-Headers'].lower()
        for header in ('ratelimit-limit', 'ratelimit-remaining', 'ratelimit-reset', 'retry-after'):
            self.assertIn(header, exposed)
        self.assertNotIn('Access-Control-Allow-Credentials', response)
        self.assertIn('origin', response['Vary'].lower())

    def test_browser_request_still_requires_authentication(self):
        url = reverse('book-list')
        # Test settings normally allow anonymous requests; exercise the real
        # production permission rather than reaching the queryset.
        with patch.object(resolve(url).func.cls, 'permission_classes', [CachedHasAPIKey]):
            response = self.client.get(url, HTTP_ORIGIN=self.origin)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Access-Control-Allow-Origin'], self.origin)

    def test_browser_request_still_enforces_quota(self):
        with (
            patch.object(CachedHasAPIKey, 'has_permission', return_value=True),
            patch.object(PerAPIKeyRateThrottle, 'allow_request', return_value=False),
        ):
            response = self.client.get(reverse('book-list'), HTTP_ORIGIN=self.origin)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response['Access-Control-Allow-Origin'], self.origin)
        self.assertIn('Retry-After', response)
