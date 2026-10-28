from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from django_redis.exceptions import ConnectionInterrupted
from rest_framework.test import APIRequestFactory

from apps.access.models import ConsumerAPIKey
from apps.core.cache_utils import api_key_validation_cache_key, api_key_validation_cache_value
from apps.core.permissions import CACHE_TTL, CachedHasAPIKey


@override_settings(API_KEY_CUSTOM_HEADER='HTTP_X_API_KEY')
class CachedHasAPIKeyTests(TestCase):
    def test_legacy_api_key_header_is_not_accepted(self):
        _, plaintext_key = ConsumerAPIKey.objects.create_key(
            name='Example App',
            consumer_name='Example App',
            email='developer@example.com',
        )
        request = APIRequestFactory().get('/api/v1/books/', HTTP_API_KEY=plaintext_key)

        self.assertFalse(CachedHasAPIKey().has_permission(request, view=None))

    def test_cached_prefix_does_not_authenticate_a_different_secret(self):
        record, plaintext_key = ConsumerAPIKey.objects.create_key(
            name='Example App',
            consumer_name='Example App',
            email='developer@example.com',
        )
        permission = CachedHasAPIKey()
        valid_request = APIRequestFactory().get(
            '/api/v1/books/',
            HTTP_X_API_KEY=plaintext_key,
        )
        self.assertTrue(permission.has_permission(valid_request, view=None))

        forged_key = f'{record.prefix}.incorrect-secret'
        forged_request = APIRequestFactory().get(
            '/auth/revoke-key/',
            HTTP_X_API_KEY=forged_key,
        )
        self.assertFalse(permission.has_permission(forged_request, view=None))

        repeated_valid_request = APIRequestFactory().get(
            '/api/v1/books/',
            HTTP_X_API_KEY=plaintext_key,
        )
        self.assertTrue(permission.has_permission(repeated_valid_request, view=None))

    def test_legacy_boolean_cache_entry_is_revalidated_before_replacement(self):
        record, plaintext_key = ConsumerAPIKey.objects.create_key(
            name='Example App',
            consumer_name='Example App',
            email='developer@example.com',
        )
        cache_key = api_key_validation_cache_key(record.prefix)
        cache.set(cache_key, True, CACHE_TTL)
        permission = CachedHasAPIKey()

        forged_request = APIRequestFactory().get(
            '/auth/revoke-key/',
            HTTP_X_API_KEY=f'{record.prefix}.incorrect-secret',
        )
        self.assertFalse(permission.has_permission(forged_request, view=None))
        self.assertIs(cache.get(cache_key), True)

        valid_request = APIRequestFactory().get(
            '/api/v1/books/',
            HTTP_X_API_KEY=plaintext_key,
        )
        self.assertTrue(permission.has_permission(valid_request, view=None))
        self.assertEqual(cache.get(cache_key), api_key_validation_cache_value(plaintext_key))

    def test_mismatched_cached_fingerprint_revalidates_valid_key(self):
        record, plaintext_key = ConsumerAPIKey.objects.create_key(
            name='Example App',
            consumer_name='Example App',
            email='developer@example.com',
        )
        cache_key = api_key_validation_cache_key(record.prefix)
        cache.set(cache_key, 'stale-fingerprint', CACHE_TTL)

        request = APIRequestFactory().get('/api/v1/books/', HTTP_X_API_KEY=plaintext_key)
        self.assertTrue(CachedHasAPIKey().has_permission(request, view=None))
        self.assertEqual(cache.get(cache_key), api_key_validation_cache_value(plaintext_key))

    def test_valid_key_falls_back_to_database_when_cache_is_unavailable(self):
        record, plaintext_key = ConsumerAPIKey.objects.create_key(
            name='Example App',
            consumer_name='Example App',
            email='developer@example.com',
        )
        request = APIRequestFactory().get('/api/v1/books/', HTTP_X_API_KEY=plaintext_key)

        with (
            patch('apps.core.permissions.cache.get', side_effect=ConnectionInterrupted(None)),
            patch('apps.core.permissions.cache.set', side_effect=ConnectionInterrupted(None)),
        ):
            allowed = CachedHasAPIKey().has_permission(request, view=None)

        self.assertTrue(allowed)
        self.assertEqual(request.api_key_prefix, record.prefix)
