import json
from types import SimpleNamespace

from django.contrib import admin
from django.test import RequestFactory, TestCase

from apps.access.admin import ConsumerAPIKeyAdmin
from apps.access.models import ConsumerAPIKey
from apps.core.logging import JsonEventFormatter


class ConsumerAPIKeyAdminLoggingTests(TestCase):
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

        with self.assertLogs('api.security', level='WARNING') as captured:
            model_admin.save_model(request, record, form=None, change=True)

        payload = json.loads(JsonEventFormatter().format(captured.records[0]))
        self.assertEqual(payload['event'], 'security.api_key.revoked')
        self.assertEqual(payload['api_key_prefix'], record.prefix)
        self.assertEqual(payload['actor_id'], 42)
        self.assertNotIn(plaintext_key, json.dumps(payload))
        self.assertNotIn(record.pk, json.dumps(payload))
