# ty: ignore[unresolved-attribute]
import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from apps.access.models import ConsumerAPIKey
from apps.access.serializers import KeyRequestSerializer, KeyResponseSerializer
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
        security_logger.info(
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
