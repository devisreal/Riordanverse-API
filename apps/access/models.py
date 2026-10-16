from django.db import models
from rest_framework_api_key.models import AbstractAPIKey


class ConsumerAPIKey(AbstractAPIKey):
    """API key with identifying information for its consumer."""

    consumer_name = models.CharField(
        max_length=150,
        help_text='Name of the application or person requesting access.',
    )
    email = models.EmailField(help_text='Contact email for the key holder.')

    class Meta(AbstractAPIKey.Meta):  # ty: ignore[invalid-attribute-override]
        verbose_name = 'Consumer API Key'
        verbose_name_plural = 'Consumer API Keys'

    def __str__(self):
        return f'{self.consumer_name} ({self.email})'
