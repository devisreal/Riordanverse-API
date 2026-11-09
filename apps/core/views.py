"""Public API discovery and process/dependency health endpoints."""

import logging

from django.conf import settings
from django.db import DatabaseError, connections
from django.urls import reverse
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.schema_serializers import HealthResponseSchemaSerializer

logger = logging.getLogger(__name__)

API_DIRECTORY_ROUTES = {
    'books': 'book-list',
    'characters': 'character-list',
    'gods': 'god-list',
    'titans': 'titan-list',
    'monsters': 'monster-list',
    'creatures': 'creature-list',
    'weapons': 'weapon-list',
    'locations': 'location-list',
    'quests': 'quest-list',
    'prophecies': 'prophecy-list',
    'events': 'event-list',
    'cabins': 'cabin-list',
    'factions': 'faction-list',
    'images': 'image-list',
    'search': 'search',
}


@extend_schema(
    auth=[],
    tags=['API Directory'],
    responses={
        200: inline_serializer(
            name='APIDirectory',
            fields={name: serializers.CharField() for name in API_DIRECTORY_ROUTES},
        ),
    },
)
class APIDirectoryView(APIView):
    """List collection and search URLs without accessing data or requiring an API key."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = ()
    renderer_classes = (JSONRenderer,)

    def get(self, request):
        return Response({name: reverse(route) for name, route in API_DIRECTORY_ROUTES.items()})


def _health_response(data, status_code=status.HTTP_200_OK):
    response = Response(data, status=status_code)
    response['Cache-Control'] = 'no-store, max-age=0'
    return response


@extend_schema(
    auth=[],
    tags=['Health'],
    responses={200: HealthResponseSchemaSerializer},
)
class HealthLiveView(APIView):
    """Report that this application process is alive and can serve requests."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = ()

    def get(self, request):
        return _health_response({'status': 'ok', 'version': settings.APP_VERSION})


@extend_schema(
    auth=[],
    tags=['Health'],
    responses={
        200: HealthResponseSchemaSerializer,
        503: HealthResponseSchemaSerializer,
    },
)
class HealthReadyView(APIView):
    """Report whether required dependencies allow this process to serve API traffic."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = ()

    def get(self, request):
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute('SELECT 1')
        except DatabaseError:
            logger.exception('Database readiness check failed.')
            return _health_response(
                {
                    'status': 'not_ready',
                    'checks': {'database': 'unavailable'},
                    'version': settings.APP_VERSION,
                },
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return _health_response(
            {
                'status': 'ok',
                'checks': {'database': 'connected'},
                'version': settings.APP_VERSION,
            }
        )
