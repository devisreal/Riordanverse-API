from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.http import HttpResponse
from django.test import SimpleTestCase
from django_redis.exceptions import ConnectionInterrupted
from rest_framework.exceptions import Throttled
from rest_framework.test import APIRequestFactory

from apps.access.views import KeyRequestThrottle
from apps.core.exceptions import custom_exception_handler
from apps.core.middleware import RateLimitHeadersMiddleware
from apps.core.throttles import _FALLBACK_THROTTLE_CACHE, PerAPIKeyRateThrottle


class TwoPerHourThrottle(PerAPIKeyRateThrottle):
    rate = '2/hour'
    anon_rate = '2/hour'


class UnavailableCache:
    def get(self, key, default=None):
        raise ConnectionInterrupted(None)

    def add(self, key, value, timeout=None):
        raise ConnectionInterrupted(None)

    def incr(self, key, delta=1):
        raise ConnectionInterrupted(None)


class CacheFallbackThrottleTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
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

    def test_per_api_key_rate_limit_falls_back_to_local_memory(self):
        throttle = TwoPerHourThrottle()
        request = APIRequestFactory().get('/api/v1/books/')
        request.api_key_prefix = 'fallbackprefix'

        for _ in range(2):
            throttle.cache = UnavailableCache()
            self.assertTrue(throttle.allow_request(request, view=None))

        throttle.cache = UnavailableCache()
        self.assertFalse(throttle.allow_request(request, view=None))
        self.assertIsInstance(throttle.cache, UnavailableCache)

    def test_per_api_key_rate_limit_is_shared_by_prefix_not_secret(self):
        throttle = TwoPerHourThrottle()
        factory = APIRequestFactory()
        first = factory.get('/api/v1/books/', HTTP_X_API_KEY='publicprefix.secret-one')
        second = factory.get('/api/v1/books/', HTTP_X_API_KEY='publicprefix.secret-two')
        other_key = factory.get('/api/v1/books/', HTTP_X_API_KEY='anotherprefix.secret')
        fourth = factory.get('/api/v1/books/', HTTP_X_API_KEY='publicprefix.secret-three')
        for request in (first, second, fourth):
            request.api_key_prefix = 'publicprefix'
        other_key.api_key_prefix = 'anotherprefix'

        self.assertTrue(throttle.allow_request(first, view=None))
        self.assertTrue(throttle.allow_request(second, view=None))
        self.assertTrue(throttle.allow_request(other_key, view=None))
        self.assertFalse(throttle.allow_request(fourth, view=None))
        self.assertEqual(fourth.rate_limit_info['remaining'], 0)
        self.assertGreater(throttle.wait(), 0)

    def test_requests_without_api_key_use_the_anonymous_ip_bucket(self):
        throttle = TwoPerHourThrottle()
        factory = APIRequestFactory()
        same_ip = [
            factory.get('/health/live/', REMOTE_ADDR='192.0.2.5'),
            factory.get(
                '/health/live/',
                HTTP_X_API_KEY='unvalidated.prefix',
                REMOTE_ADDR='192.0.2.5',
            ),
            factory.get('/health/live/', REMOTE_ADDR='192.0.2.5'),
        ]
        other_ip = factory.get('/health/live/', REMOTE_ADDR='192.0.2.6')

        self.assertTrue(throttle.allow_request(same_ip[0], view=None))
        self.assertTrue(throttle.allow_request(same_ip[1], view=None))
        self.assertFalse(throttle.allow_request(same_ip[2], view=None))
        self.assertTrue(throttle.allow_request(other_ip, view=None))

    def test_rate_limit_headers_are_attached_to_responses(self):
        request = APIRequestFactory().get(
            '/api/v1/books/',
            HTTP_X_API_KEY='headersprefix.secret',
        )
        request.api_key_prefix = 'headersprefix'
        throttle = TwoPerHourThrottle()
        self.assertTrue(throttle.allow_request(request, view=None))

        middleware = RateLimitHeadersMiddleware(lambda _request: HttpResponse())
        response = middleware(request)

        self.assertEqual(response['RateLimit-Limit'], '2;w=3600')
        self.assertEqual(response['RateLimit-Remaining'], '1')
        self.assertGreaterEqual(int(response['RateLimit-Reset']), 1)

    def test_exhausted_quota_still_emits_reset_headers(self):
        throttle = TwoPerHourThrottle()
        middleware = RateLimitHeadersMiddleware(lambda _request: HttpResponse())
        factory = APIRequestFactory()
        responses = []

        for _ in range(3):
            request = factory.get('/api/v1/books/', HTTP_X_API_KEY='limitedprefix.secret')
            request.api_key_prefix = 'limitedprefix'
            throttle.allow_request(request, view=None)
            responses.append(middleware(request))

        self.assertEqual(responses[-1]['RateLimit-Remaining'], '0')
        self.assertGreaterEqual(int(responses[-1]['RateLimit-Reset']), 1)

    def test_throttled_errors_keep_retry_after_header(self):
        response = custom_exception_handler(Throttled(wait=7), {'request': self.request})

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response['Retry-After'], '7')
