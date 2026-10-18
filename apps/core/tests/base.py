from django.test import TestCase
from rest_framework.test import APIClient


class BaseAPITestCase(TestCase):
    """Shared Django REST Framework API test case with a configured client."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
