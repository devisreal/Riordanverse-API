import logging

from django.contrib import admin
from rest_framework_api_key.admin import APIKeyModelAdmin

from apps.access.models import ConsumerAPIKey
from apps.core.logging import SUCCESS_LEVEL

security_logger = logging.getLogger('api.security')


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

    def save_model(self, request, obj, form, change):
        created = not obj.pk
        was_revoked = (
            self.model.objects.filter(pk=obj.pk).values_list('revoked', flat=True).first()
            if obj.pk
            else False
        )
        super().save_model(request, obj, form, change)

        if created:
            event = 'security.api_key.created'
            message = 'security.api_key.created'
            level = SUCCESS_LEVEL
        elif obj.revoked and not was_revoked:
            event = 'security.api_key.revoked'
            message = 'security.api_key.revoked'
            level = logging.WARNING
        else:
            return

        security_logger.log(
            level,
            message,
            extra={
                'event': event,
                'request_id': getattr(request, 'request_id', None),
                'api_key_prefix': obj.prefix,
                'actor_id': getattr(getattr(request, 'user', None), 'pk', None),
            },
        )
