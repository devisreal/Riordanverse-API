# ty: ignore[unresolved-attribute]
import logging

from django.db import transaction
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from apps.access.models import ConsumerAPIKey
from apps.access.serializers import (
    KeyRequestSerializer,
    KeyResponseSerializer,
    KeyRevocationResponseSerializer,
    KeyVerificationResponseSerializer,
)
from apps.access.services import schedule_api_key_revocation_side_effects
from apps.core.logging import SUCCESS_LEVEL
from apps.core.permissions import CachedHasAPIKey
from apps.core.schema_serializers import ErrorEnvelopeSchemaSerializer
from apps.core.throttles import CacheFallbackAnonRateThrottle

security_logger = logging.getLogger('api.security')


class KeyRequestThrottle(CacheFallbackAnonRateThrottle):
    """Limit self-service key requests by client IP, even during Redis outages."""

    scope = 'key_request'
    rate = '5/hour'


class KeyVerificationThrottle(CacheFallbackAnonRateThrottle):
    """Limit public key verification attempts by client IP."""

    scope = 'key_verification'
    rate = '5/hour'


@extend_schema(
    auth=[],
    tags=['Authentication'],
    request=None,
    parameters=[
        OpenApiParameter(
            name='X-API-Key',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            required=False,
            description='The key to verify. Omit it to receive `valid: false`.',
        ),
    ],
    responses={
        200: KeyVerificationResponseSerializer,
        429: ErrorEnvelopeSchemaSerializer,
    },
)
class VerifyKeyView(APIView):
    """Check a supplied API key directly against the database."""

    permission_classes = (AllowAny,)
    throttle_classes = (KeyVerificationThrottle,)

    def post(self, request):
        key = HasAPIKey().get_key(request)
        try:
            api_key = ConsumerAPIKey.objects.get_from_key(key) if key else None
        except ConsumerAPIKey.DoesNotExist, ValueError:
            api_key = None

        is_valid = bool(api_key and not api_key.has_expired)
        if not is_valid:
            if not key:
                reason = 'missing_key'
            elif '.' not in key:
                reason = 'malformed_key'
            elif api_key is None:
                reason = 'invalid_or_revoked_key'
            else:
                reason = 'expired_key'
            security_logger.warning(
                'security.api_key.verification_failed',
                extra={
                    'event': 'security.api_key.verification_failed',
                    'request_id': getattr(request, 'request_id', None),
                    'api_key_prefix': key.partition('.')[0] if key and '.' in key else None,
                    'reason': reason,
                },
            )
        return Response(
            {
                'valid': is_valid,
                'consumer_name': api_key.consumer_name if is_valid else None,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    auth=[],
    tags=['Authentication'],
    request=KeyRequestSerializer,
    responses={
        201: KeyResponseSerializer,
        400: ErrorEnvelopeSchemaSerializer,
        429: ErrorEnvelopeSchemaSerializer,
    },
)
class RequestKeyView(APIView):
    """Issue a consumer API key and display its plaintext value once."""

    permission_classes = (AllowAny,)
    throttle_classes = (KeyRequestThrottle,)

    def post(self, request):
        serializer = KeyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        consumer_name = serializer.validated_data['consumer_name']

        api_key, plaintext_key = ConsumerAPIKey.objects.create_key(
            consumer_name=consumer_name,
            email=serializer.validated_data['email'],
            name=consumer_name[:50],
        )
        security_logger.log(
            SUCCESS_LEVEL,
            'security.api_key.created',
            extra={
                'event': 'security.api_key.created',
                'request_id': getattr(request, 'request_id', None),
                'api_key_prefix': api_key.prefix,
            },
        )

        response_data = KeyResponseSerializer(
            {
                'api_key': plaintext_key,
                'consumer_name': api_key.consumer_name,
                'email': api_key.email,
                'message': (
                    'Your API key has been created. Store it securely; it will not be shown again.'
                ),
            }
        ).data
        return Response(response_data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Authentication'],
    request=None,
    responses={
        200: KeyRevocationResponseSerializer,
        400: ErrorEnvelopeSchemaSerializer,
        403: ErrorEnvelopeSchemaSerializer,
        429: ErrorEnvelopeSchemaSerializer,
    },
)
class RevokeAPIKeyView(APIView):
    """Revoke only the API key used to authenticate this request."""

    permission_classes = (CachedHasAPIKey,)

    @transaction.atomic
    def post(self, request):
        if request.data:
            raise ValidationError('This endpoint does not accept a request body.')

        raw_request = getattr(request, '_request', request)
        prefix = getattr(raw_request, 'api_key_prefix', None)
        if not prefix:
            raise PermissionDenied('The authenticated API key could not be identified.')

        api_key = ConsumerAPIKey.objects.select_for_update().filter(prefix=prefix).first()
        if api_key is None:
            raise PermissionDenied('The authenticated API key is no longer available.')

        was_revoked = api_key.revoked
        if not was_revoked:
            api_key.revoked = True
            api_key.save(update_fields=['revoked'])

        schedule_api_key_revocation_side_effects(
            prefix,
            request_id=getattr(request, 'request_id', None),
            actor_id=None,
            log_event=not was_revoked,
        )
        message = (
            'Your API key has already been revoked.' if was_revoked else 'Your API key was revoked.'
        )
        return Response(
            KeyRevocationResponseSerializer({'revoked': True, 'message': message}).data,
            status=status.HTTP_200_OK,
        )
