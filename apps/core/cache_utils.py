"""Shared exception types for gracefully handling an unavailable Redis cache."""

from django_redis.exceptions import ConnectionInterrupted
from redis.exceptions import RedisError

CACHE_UNAVAILABLE_EXCEPTIONS = (ConnectionInterrupted, RedisError)
