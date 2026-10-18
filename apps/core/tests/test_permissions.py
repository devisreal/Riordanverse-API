from unittest.mock import patch

from django.test import TestCase, override_settings
from django_redis.exceptions import ConnectionInterrupted
from rest_framework.test import APIRequestFactory

from apps.access.models import ConsumerAPIKey
from apps.core.permissions import CachedHasAPIKey


@override_settings(API_KEY_CUSTOM_HEADER='HTTP_API_KEY')
class CachedHasAPIKeyTests(TestCase):
    def test_valid_key_falls_back_to_database_when_cache_is_unavailable(self):
        _, plaintext_key = ConsumerAPIKey.objects.create_key(
            name='Example App',
            consumer_name='Example App',
            email='developer@example.com',
        )
        request = APIRequestFactory().get('/api/v1/books/', HTTP_API_KEY=plaintext_key)

        with (
            patch('apps.core.permissions.cache.get', side_effect=ConnectionInterrupted(None)),
            patch('apps.core.permissions.cache.set', side_effect=ConnectionInterrupted(None)),
        ):
            allowed = CachedHasAPIKey().has_permission(request, view=None)

        self.assertTrue(allowed)
