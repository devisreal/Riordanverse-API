import logging

from django.db import transaction

from apps.core.cache_utils import invalidate_api_key_validation_cache

security_logger = logging.getLogger('api.security')


def schedule_api_key_revocation_side_effects(
    prefix: str,
    *,
    request_id: str | None,
    actor_id: int | None,
    log_event: bool = True,
) -> None:
    """Invalidate a revoked key's cache and emit its audit event after commit."""

    def after_commit():
        invalidate_api_key_validation_cache(prefix)
        if log_event:
            security_logger.warning(
                'security.api_key.revoked',
                extra={
                    'event': 'security.api_key.revoked',
                    'request_id': request_id,
                    'api_key_prefix': prefix,
                    'actor_id': actor_id,
                },
            )

    transaction.on_commit(after_commit)
