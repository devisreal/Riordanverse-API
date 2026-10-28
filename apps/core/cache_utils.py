"""Shared API-key cache helpers and graceful Redis-outage handling."""

import logging

from django.core.cache import cache
from django.utils.crypto import salted_hmac
from django_redis.exceptions import ConnectionInterrupted
from redis.exceptions import RedisError

CACHE_UNAVAILABLE_EXCEPTIONS = (ConnectionInterrupted, RedisError)
API_KEY_CACHE_PREFIX = 'api_key:'

logger = logging.getLogger(__name__)


def api_key_validation_cache_key(prefix: str) -> str:
    return f'{API_KEY_CACHE_PREFIX}{prefix}'


def api_key_validation_cache_value(key: str) -> str:
    """Fingerprint a key so a prefix cache hit still verifies the supplied secret."""
    return salted_hmac(
        'apps.core.api_key_validation_cache',
        key,
        algorithm='sha256',
    ).hexdigest()


def invalidate_api_key_validation_cache(prefix: str) -> None:
    """Drop a cached positive API-key validation after the key is revoked."""
    try:
        cache.delete(api_key_validation_cache_key(prefix))
    except CACHE_UNAVAILABLE_EXCEPTIONS:
        logger.warning(
            'API-key validation cache invalidation failed; the entry will expire by TTL.',
            extra={
                'event': 'security.api_key.cache_invalidation_failed',
                'api_key_prefix': prefix,
            },
        )
