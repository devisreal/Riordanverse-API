from rest_framework.permissions import BasePermission


class CachedHasAPIKey(BasePermission):
    """Deny requests until the Redis-backed API-key permission is implemented."""

    def has_permission(self, request, view):
        return False
