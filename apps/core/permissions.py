from django.core.cache import cache
from rest_framework.permissions import BasePermission
from rest_framework_api_key.permissions import HasAPIKey

from apps.access.models import ConsumerAPIKey

CACHE_PREFIX = 'api_key:'
CACHE_TTL = 60 * 5


class CachedHasAPIKey(BasePermission):
    """Validate API keys with a short-lived cache of validation decisions."""

    def has_permission(self, request, view):
        key = HasAPIKey().get_key(request)
        if not key:
            return False

        # The library's prefix is public/non-secret and uniquely identifies a key.
        prefix, separator, _ = key.partition('.')
        if not separator:
            return False

        cache_key = f'{CACHE_PREFIX}{prefix}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        is_valid = ConsumerAPIKey.objects.is_valid(key)
        # Do not cache failures: otherwise an invalid attempt using a real
        # prefix could poison the cache and deny the legitimate key holder.
        if is_valid:
            cache.set(cache_key, True, CACHE_TTL)
        return is_valid
