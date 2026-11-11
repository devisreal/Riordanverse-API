from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from apps.core.throttles import _FALLBACK_THROTTLE_CACHE


class BaseAPITestCase(TestCase):
    """Shared Django REST Framework API test case with a configured client."""

    def setUp(self):
        super().setUp()
        cache.clear()
        _FALLBACK_THROTTLE_CACHE.clear()
        self.client = APIClient()
