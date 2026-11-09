from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework.renderers import JSONRenderer
from rest_framework.schemas.generators import EndpointEnumerator
from rest_framework.views import APIView

from apps.access.models import ConsumerAPIKey
from apps.core.permissions import CachedHasAPIKey
from apps.core.tests.base import BaseAPITestCase
from tests.makers import make_character

BROWSER_ACCEPT = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'


class VersionedRendererConfigurationTests(SimpleTestCase):
    def test_every_versioned_view_only_supports_json(self):
        endpoints = [
            (path, callback)
            for path, _, callback in EndpointEnumerator().get_api_endpoints()
            if path.startswith('/api/v1/')
        ]
        self.assertTrue(endpoints)
        for path, callback in endpoints:
            with self.subTest(path=path):
                view = callback.cls(**callback.initkwargs)
                self.assertEqual(
                    [type(renderer) for renderer in view.get_renderers()], [JSONRenderer]
                )


class JSONResponseTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.character = make_character(name='Percy Jackson')
        _, key = ConsumerAPIKey.objects.create_key(
            name='Renderer tests', consumer_name='Renderer tests', email='renderer@example.com'
        )
        self.client.credentials(HTTP_X_API_KEY=key)

    def test_browser_gets_json_for_directory_collections_details_subresources_and_search(self):
        urls = [
            reverse('api-directory'),
            reverse('character-list'),
            reverse('character-detail', kwargs={'slug': self.character.slug}),
            reverse('character-image-list', kwargs={'slug': self.character.slug}),
            reverse('character-power-list', kwargs={'slug': self.character.slug}),
            reverse('search') + '?q=Percy',
        ]
        with patch.object(APIView, 'permission_classes', [CachedHasAPIKey]):
            for url in urls:
                with self.subTest(url=url):
                    response = self.client.get(url, HTTP_ACCEPT=BROWSER_ACCEPT)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response['Content-Type'], 'application/json')
                    response.json()
                    self.assertNotIn(b'<html', response.content.lower())

    def test_browser_without_key_gets_json_forbidden_response(self):
        self.client.credentials()
        with patch.object(APIView, 'permission_classes', [CachedHasAPIKey]):
            response = self.client.get(reverse('character-list'), HTTP_ACCEPT=BROWSER_ACCEPT)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['error']['code'], 'FORBIDDEN')

    def test_browser_gets_json_error_responses(self):
        cases = [
            (reverse('character-list') + '?status=invalid', 400, 'INVALID_FILTER_VALUE'),
            (reverse('character-detail', kwargs={'slug': 'not-found'}), 404, 'NOT_FOUND'),
        ]
        with patch.object(APIView, 'permission_classes', [CachedHasAPIKey]):
            for url, status_code, error_code in cases:
                with self.subTest(url=url):
                    response = self.client.get(url, HTTP_ACCEPT=BROWSER_ACCEPT)
                    self.assertEqual(response.status_code, status_code)
                    self.assertEqual(response['Content-Type'], 'application/json')
                    self.assertEqual(response.json()['error']['code'], error_code)

    def test_html_only_accept_is_rejected_with_json_not_a_browsable_page(self):
        response = self.client.get(reverse('character-list'), HTTP_ACCEPT='text/html')

        self.assertEqual(response.status_code, 406)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('error', response.json())

    def test_browsable_api_format_is_no_longer_available(self):
        response = self.client.get(reverse('character-list'), {'format': 'api'})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['error']['code'], 'NOT_FOUND')
