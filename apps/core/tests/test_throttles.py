from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase
from django_redis.exceptions import ConnectionInterrupted
from rest_framework.test import APIRequestFactory

from apps.access.views import KeyRequestThrottle
from apps.core.throttles import _FALLBACK_THROTTLE_CACHE


class UnavailableCache:
    def get(self, key, default=None):
        raise ConnectionInterrupted(None)


class CacheFallbackThrottleTests(SimpleTestCase):
    def setUp(self):
        _FALLBACK_THROTTLE_CACHE.clear()
        self.request = APIRequestFactory().post('/auth/request-key/', REMOTE_ADDR='192.0.2.1')
        self.request.user = AnonymousUser()

    def test_key_request_throttle_falls_back_to_local_memory(self):
        throttle = KeyRequestThrottle()
        throttle.cache = UnavailableCache()

        self.assertTrue(throttle.allow_request(self.request, view=None))
        self.assertIsInstance(throttle.cache, UnavailableCache)

    def test_fallback_still_enforces_the_key_request_limit(self):
        throttle = KeyRequestThrottle()
        throttle.cache = UnavailableCache()

        for _ in range(5):
            self.assertTrue(throttle.allow_request(self.request, view=None))
            throttle.cache = UnavailableCache()

        self.assertFalse(throttle.allow_request(self.request, view=None))
