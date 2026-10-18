from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django_redis.exceptions import ConnectionInterrupted
from rest_framework.test import APIClient


class RequestKeyViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch(
        'rest_framework.throttling.default_cache.get',
        side_effect=ConnectionInterrupted(None),
    )
    def test_request_key_succeeds_when_redis_is_unavailable(self, _cache_get):
        response = self.client.post(
            reverse('request-api-key'),
            {'consumer_name': 'Example App', 'email': 'developer@example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn('api_key', response.data)
