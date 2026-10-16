# ty: ignore[unresolved-attribute]
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.access.models import ConsumerAPIKey
from apps.access.serializers import KeyRequestSerializer, KeyResponseSerializer


class KeyRequestThrottle(AnonRateThrottle):
    """Limit self-service key requests by client IP."""

    rate = '5/hour'


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
