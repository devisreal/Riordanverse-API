from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django_redis.exceptions import ConnectionInterrupted
from rest_framework.test import APIClient

from apps.access.models import ConsumerAPIKey
from apps.core.throttles import _FALLBACK_THROTTLE_CACHE


class RequestKeyViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()
        _FALLBACK_THROTTLE_CACHE.clear()

    def _request_key(self, data=None):
        return self.client.post(
            reverse('request-api-key'),
            data or {'consumer_name': 'Test App', 'email': 'test@example.com'},
            format='json',
        )

    def test_post_valid_data_returns_201(self):
        response = self._request_key()
        self.assertEqual(response.status_code, 201)

    def test_post_returns_api_key_in_response(self):
        response = self._request_key()
        self.assertIn('api_key', response.data)
        self.assertIsNotNone(response.data['api_key'])

    def test_post_returns_consumer_name(self):
        response = self._request_key()
        self.assertEqual(response.data['consumer_name'], 'Test App')

    def test_post_returns_message(self):
        response = self._request_key()
        self.assertIn('message', response.data)

    def test_post_missing_email_returns_400(self):
        response = self._request_key({'consumer_name': 'Test App'})
        self.assertEqual(response.status_code, 400)

    def test_post_missing_consumer_name_returns_400(self):
        response = self._request_key({'email': 'test@example.com'})
        self.assertEqual(response.status_code, 400)

    def test_post_invalid_email_returns_400(self):
        response = self._request_key({'consumer_name': 'Test App', 'email': 'not-an-email'})
        self.assertEqual(response.status_code, 400)

    def test_key_is_not_stored_in_plaintext(self):
        response = self._request_key()
        stored_key = ConsumerAPIKey.objects.get()

        self.assertNotEqual(stored_key.prefix, response.data['api_key'])
        self.assertNotIn('.', stored_key.prefix)

    @patch(
        'rest_framework.throttling.default_cache.get',
        side_effect=ConnectionInterrupted(None),
    )
    def test_post_succeeds_when_redis_is_unavailable(self, _cache_get):
        response = self._request_key()
        self.assertEqual(response.status_code, 201)
        self.assertIn('api_key', response.data)
