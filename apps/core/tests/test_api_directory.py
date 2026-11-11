from typing import ClassVar
from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import get_script_prefix, resolve, reverse, set_script_prefix
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView

from apps.core.permissions import CachedHasAPIKey
from apps.core.views import APIDirectoryView


class APIDirectoryTests(SimpleTestCase):
    # SimpleTestCase forbids database queries, including on unauthenticated requests.
    expected_routes: ClassVar[dict[str, str]] = {
        'books': 'book-list',
        'characters': 'character-list',
        'gods': 'god-list',
        'titans': 'titan-list',
        'monsters': 'monster-list',
        'creatures': 'creature-list',
        'weapons': 'weapon-list',
        'locations': 'location-list',
        'quests': 'quest-list',
        'prophecies': 'prophecy-list',
        'events': 'event-list',
        'cabins': 'cabin-list',
        'factions': 'faction-list',
        'images': 'image-list',
        'search': 'search',
    }

    def setUp(self):
        self.client = APIClient()

    def test_directory_is_public_json_and_contains_all_collection_links(self):
        with patch.object(APIView, 'permission_classes', [CachedHasAPIKey]):
            response = self.client.get(reverse('api-directory'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(reverse('api-directory'), '/api/v1/')
        self.assertEqual(
            response.json(),
            {name: reverse(route) for name, route in self.expected_routes.items()},
        )
        self.assertNotIn('meta', response.json())
        for name, url in response.json().items():
            with self.subTest(collection=name):
                self.assertTrue(url.endswith('/'))
                self.assertEqual(resolve(url).url_name, self.expected_routes[name])
                self.assertIsNot(resolve(url).func.view_class, APIDirectoryView)

    def test_directory_does_not_validate_keys_or_use_cache(self):
        with (
            patch('apps.core.permissions.CachedHasAPIKey.has_permission') as permission,
            patch('apps.core.throttles.PerAPIKeyRateThrottle.allow_request') as throttle,
            patch('django.core.cache.cache.get', side_effect=RuntimeError('Cache unavailable')),
            patch('django.core.cache.cache.set', side_effect=RuntimeError('Cache unavailable')),
        ):
            response = self.client.get(
                reverse('api-directory'),
                HTTP_X_API_KEY='invalid.key',
                HTTP_AUTHORIZATION='Basic invalid',
            )

        self.assertEqual(response.status_code, 200)
        permission.assert_not_called()
        throttle.assert_not_called()
        self.assertNotIn('RateLimit-Limit', response)

    def test_linked_collections_and_search_still_require_an_api_key(self):
        with patch.object(APIView, 'permission_classes', [CachedHasAPIKey]):
            for route in self.expected_routes.values():
                with self.subTest(route=route):
                    response = self.client.get(reverse(route))
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(response.json()['error']['code'], 'FORBIDDEN')

    def test_directory_head_is_supported(self):
        response = self.client.head(reverse('api-directory'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_directory_rejects_writes(self):
        for method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            with self.subTest(method=method):
                response = self.client.generic(method, reverse('api-directory'))
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response.json()['error']['code'], 'METHOD_NOT_ALLOWED')

    def test_directory_returns_json_for_browser_accept_header(self):
        response = self.client.get(
            reverse('api-directory'), HTTP_ACCEPT='text/html,application/xhtml+xml,*/*;q=0.8'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_directory_honors_script_prefix(self):
        original_prefix = get_script_prefix()
        try:
            set_script_prefix('/archive/')
            response = APIDirectoryView.as_view()(APIRequestFactory().get('/api/v1/'))
            self.assertEqual(response.data['books'], '/archive/api/v1/books/')
        finally:
            set_script_prefix(original_prefix)
