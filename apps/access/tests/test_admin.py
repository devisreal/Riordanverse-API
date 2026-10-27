import json
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib import admin
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django_redis.exceptions import ConnectionInterrupted
from rest_framework.test import APIRequestFactory

from apps.access.admin import ConsumerAPIKeyAdmin
from apps.access.models import ConsumerAPIKey
from apps.core.cache_utils import api_key_validation_cache_key
from apps.core.logging import JsonEventFormatter
from apps.core.permissions import CACHE_TTL, CachedHasAPIKey


class ConsumerAPIKeyAdminLoggingTests(TestCase):
    def test_creation_uses_success_level_without_logging_key_material(self):
        record = ConsumerAPIKey(
            consumer_name='Test App',
            email='test@example.com',
            name='Test App',
        )
        request = RequestFactory().post('/admin/access/consumerapikey/')
        request.user = SimpleNamespace(pk=42)
        model_admin = ConsumerAPIKeyAdmin(ConsumerAPIKey, admin.site)

        with (
            patch('rest_framework_api_key.admin.messages.add_message') as add_message,
            self.assertLogs('api.security', level='INFO') as captured,
        ):
            model_admin.save_model(request, record, form=None, change=False)

        payload = json.loads(JsonEventFormatter().format(captured.records[0]))
        self.assertEqual(payload['event'], 'security.api_key.created')
        self.assertEqual(payload['level'], 'SUCCESS')
        self.assertEqual(payload['api_key_prefix'], record.prefix)
        self.assertNotIn(record.pk, json.dumps(payload))
        self.assertNotIn(str(add_message.call_args.args[2]), json.dumps(payload))

    def test_revocation_invalidates_cached_key_after_commit(self):
        record, plaintext_key = ConsumerAPIKey.objects.create_key(
            consumer_name='Test App',
            email='test@example.com',
            name='Test App',
        )
        cache_key = api_key_validation_cache_key(record.prefix)
        cache.set(cache_key, True, CACHE_TTL)
        self.assertTrue(cache.get(cache_key))

        record.revoked = True
        request = RequestFactory().post('/admin/access/consumerapikey/')
        request.user = SimpleNamespace(pk=42)
        model_admin = ConsumerAPIKeyAdmin(ConsumerAPIKey, admin.site)

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            model_admin.save_model(request, record, form=None, change=True)

        self.assertEqual(len(callbacks), 1)
        self.assertIsNone(cache.get(cache_key))
        api_request = APIRequestFactory().get('/api/v1/books/', HTTP_X_API_KEY=plaintext_key)
        self.assertFalse(CachedHasAPIKey().has_permission(api_request, view=None))

    def test_cache_invalidation_waits_for_database_commit(self):
        record, _plaintext_key = ConsumerAPIKey.objects.create_key(
            consumer_name='Test App',
            email='test@example.com',
            name='Test App',
        )
        cache_key = api_key_validation_cache_key(record.prefix)
        cache.set(cache_key, True, CACHE_TTL)
        self.addCleanup(cache.delete, cache_key)
        record.revoked = True
        request = RequestFactory().post('/admin/access/consumerapikey/')
        request.user = SimpleNamespace(pk=42)
        model_admin = ConsumerAPIKeyAdmin(ConsumerAPIKey, admin.site)

        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            model_admin.save_model(request, record, form=None, change=True)
            self.assertTrue(cache.get(cache_key))

        self.assertEqual(len(callbacks), 1)
        self.assertTrue(cache.get(cache_key))

    def test_cache_unavailable_does_not_block_admin_revocation(self):
        record, _plaintext_key = ConsumerAPIKey.objects.create_key(
            consumer_name='Test App',
            email='test@example.com',
            name='Test App',
        )
        record.revoked = True
        request = RequestFactory().post('/admin/access/consumerapikey/')
        request.user = SimpleNamespace(pk=42)
        model_admin = ConsumerAPIKeyAdmin(ConsumerAPIKey, admin.site)

        with (
            patch(
                'apps.core.cache_utils.cache.delete',
                side_effect=ConnectionInterrupted(None),
            ),
            self.assertLogs('apps.core.cache_utils', level='WARNING'),
            self.captureOnCommitCallbacks(execute=True),
        ):
            model_admin.save_model(request, record, form=None, change=True)

        record.refresh_from_db()
        self.assertTrue(record.revoked)

    def test_revocation_logs_prefix_and_actor_without_plaintext_key(self):
        record, plaintext_key = ConsumerAPIKey.objects.create_key(
            consumer_name='Test App',
            email='test@example.com',
            name='Test App',
        )
        record.revoked = True
        request = RequestFactory().post('/admin/access/consumerapikey/')
        request.user = SimpleNamespace(pk=42)
        model_admin = ConsumerAPIKeyAdmin(ConsumerAPIKey, admin.site)

        with (
            self.assertLogs('api.security', level='WARNING') as captured,
            self.captureOnCommitCallbacks(execute=True),
        ):
            model_admin.save_model(request, record, form=None, change=True)

        payload = json.loads(JsonEventFormatter().format(captured.records[0]))
        self.assertEqual(payload['event'], 'security.api_key.revoked')
        self.assertEqual(payload['api_key_prefix'], record.prefix)
        self.assertEqual(payload['actor_id'], 42)
        self.assertNotIn(plaintext_key, json.dumps(payload))
        self.assertNotIn(record.pk, json.dumps(payload))
