from django.contrib import admin
from rest_framework_api_key.admin import APIKeyModelAdmin

from apps.access.models import ConsumerAPIKey


@admin.register(ConsumerAPIKey)
class ConsumerAPIKeyAdmin(APIKeyModelAdmin):
    list_display = (
        'consumer_name',
        'email',
        'created',
        'expiry_date',
        'has_expired',
        'revoked',
    )
    list_filter = ('revoked',)
    search_fields = ('consumer_name', 'email', 'name', 'prefix')
