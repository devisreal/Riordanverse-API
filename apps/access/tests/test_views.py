import json
from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django_redis.exceptions import ConnectionInterrupted
from rest_framework.test import APIClient

from apps.access.models import ConsumerAPIKey
from apps.core.logging import JsonEventFormatter
from apps.core.throttles import _FALLBACK_THROTTLE_CACHE


class VerifyKeyViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()
        _FALLBACK_THROTTLE_CACHE.clear()

    def _verify_key(self, key=None):
        extra = {'HTTP_X_API_KEY': key} if key is not None else {}
        return self.client.post(reverse('verify-api-key'), **extra)

    def _create_key(self):
        return ConsumerAPIKey.objects.create_key(
            consumer_name='Test App',
            email='test@example.com',
            name='Test App',
        )

    def test_valid_key_returns_true_and_consumer_name(self):
        _record, plaintext_key = self._create_key()

        response = self._verify_key(plaintext_key)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'valid': True, 'consumer_name': 'Test App'})

    def test_invalid_key_returns_false_without_name(self):
        response = self._verify_key('invalid.key')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'valid': False, 'consumer_name': None})

    def test_failed_verification_logs_prefix_but_never_plaintext_key(self):
        plaintext_key = 'testprefix.super-secret-value'

        with self.assertLogs('api.security', level='WARNING') as captured:
            response = self._verify_key(plaintext_key)

        self.assertEqual(response.data, {'valid': False, 'consumer_name': None})
        payload = json.loads(JsonEventFormatter().format(captured.records[0]))
        self.assertEqual(payload['event'], 'security.api_key.verification_failed')
        self.assertEqual(payload['api_key_prefix'], 'testprefix')
        self.assertNotIn(plaintext_key, json.dumps(payload))
        self.assertNotIn('super-secret-value', json.dumps(payload))

    def test_missing_key_returns_false_without_name(self):
        response = self._verify_key()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'valid': False, 'consumer_name': None})

    def test_revoked_key_returns_false_without_name(self):
        record, plaintext_key = self._create_key()
        record.revoked = True
        record.save(update_fields=['revoked'])

        response = self._verify_key(plaintext_key)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'valid': False, 'consumer_name': None})

    def test_expired_key_returns_false_without_name(self):
        record, plaintext_key = self._create_key()
        record.expiry_date = timezone.now() - timedelta(days=1)
        record.save(update_fields=['expiry_date'])

        response = self._verify_key(plaintext_key)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'valid': False, 'consumer_name': None})


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

    def test_key_creation_logs_prefix_but_never_plaintext_key(self):
        with self.assertLogs('api.security', level='INFO') as captured:
            response = self._request_key()

        payload = json.loads(JsonEventFormatter().format(captured.records[0]))
        key_record = ConsumerAPIKey.objects.get()
        self.assertEqual(payload['event'], 'security.api_key.created')
        self.assertEqual(payload['level'], 'SUCCESS')
        self.assertIn('api_key_prefix', payload)
        self.assertNotIn(response.data['api_key'], json.dumps(payload))
        self.assertNotIn(key_record.pk, json.dumps(payload))

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
