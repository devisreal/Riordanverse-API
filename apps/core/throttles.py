"""DRF throttles that degrade to process-local limits if Redis is unavailable."""

import logging

from django.core.cache.backends.locmem import LocMemCache
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

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
