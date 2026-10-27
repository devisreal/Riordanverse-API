"""DRF throttles that degrade to process-local limits if Redis is unavailable."""

import logging
import math

from django.core.cache.backends.locmem import LocMemCache
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle

from apps.core.cache_utils import CACHE_UNAVAILABLE_EXCEPTIONS

logger = logging.getLogger(__name__)

# A process-local fallback keeps requests available during a Redis outage. It is
# intentionally not a distributed limit; Redis-backed limits resume when Redis
# is reachable again.
_FALLBACK_THROTTLE_CACHE = LocMemCache('api-throttle-fallback', {})


class CacheFallbackThrottleMixin:
    """Retry a throttle check against local memory when the shared cache fails."""

    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except CACHE_UNAVAILABLE_EXCEPTIONS:
            logger.warning('Redis unavailable for DRF throttling; using local-memory fallback.')
            redis_cache = self.cache
            self.cache = _FALLBACK_THROTTLE_CACHE
            try:
                return super().allow_request(request, view)
            finally:
                self.cache = redis_cache


class CacheFallbackAnonRateThrottle(CacheFallbackThrottleMixin, AnonRateThrottle):
    """Anonymous-user throttle with a process-local outage fallback."""


class CacheFallbackUserRateThrottle(CacheFallbackThrottleMixin, UserRateThrottle):
    """Authenticated-user throttle with a process-local outage fallback."""


class PerAPIKeyRateThrottle(SimpleRateThrottle):
    """Apply a shared fixed-window quota to each API-key prefix.

    Requests without an API key use the lower anonymous IP limit. Public key
    issuance and verification views override this throttle with their own
    stricter IP-based throttles.
    """

    scope = 'api_key'
    rate = None
    anon_rate = None

    def __init__(self):
        super().__init__()
        anon_rate = self.anon_rate or self.THROTTLE_RATES.get('anon', '100/day')
        self.anon_num_requests, self.anon_duration = self.parse_rate(anon_rate)
        self.limit = self.num_requests
        self.window = self.duration
        self.remaining = self.limit
        self.reset_seconds = self.window

    def _request_bucket(self, request):
        raw_request = getattr(request, '_request', request)
        prefix = getattr(raw_request, 'api_key_prefix', None)
        if prefix:
            return 'api_key', prefix, self.num_requests, self.duration

        return 'anon', self.get_ident(request), self.anon_num_requests, self.anon_duration

    def _increment_window(self, scope, identifier, duration):
        """Atomically increment the fixed-window counter, recovering at expiry."""
        for _ in range(3):
            now = self.timer()
            window_start = int(now // duration) * duration
            window_end = window_start + duration
            timeout = max(1, math.ceil(window_end - now))
            cache_key = self.cache_format % {
                'scope': scope,
                'ident': f'{identifier}_{window_start}',
            }
            try:
                if self.cache.add(cache_key, 1, timeout=timeout):
                    return 1, max(0, math.ceil(window_end - now))
                count = self.cache.incr(cache_key)
                return count, max(0, math.ceil(window_end - now))
            except ValueError:
                # A window can expire between add() and incr(); recompute the
                # current window and retry instead of turning that race into 500.
                continue

        raise RuntimeError('Could not initialize API rate-limit counter.')

    def _allow_request(self, request):
        scope, identifier, limit, duration = self._request_bucket(request)
        count, reset_seconds = self._increment_window(scope, identifier, duration)

        self.limit = limit
        self.window = duration
        self.remaining = max(0, limit - count)
        self.reset_seconds = reset_seconds
        request_object = getattr(request, '_request', request)
        request_object.rate_limit_info = {
            'limit': limit,
            'remaining': self.remaining,
            'reset': reset_seconds,
            'window': duration,
        }
        return count <= limit

    def allow_request(self, request, view):
        try:
            return self._allow_request(request)
        except CACHE_UNAVAILABLE_EXCEPTIONS:
            logger.warning('Redis unavailable for API-key throttling; using local-memory fallback.')
            redis_cache = self.cache
            self.cache = _FALLBACK_THROTTLE_CACHE
            try:
                return self._allow_request(request)
            finally:
                self.cache = redis_cache

    def wait(self):
        return self.reset_seconds
