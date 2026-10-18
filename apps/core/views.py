"""Health endpoints for process liveness and dependency readiness."""

import logging

from django.conf import settings
from django.db import DatabaseError, connections
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


def _health_response(data, status_code=status.HTTP_200_OK):
    response = Response(data, status=status_code)
    response['Cache-Control'] = 'no-store, max-age=0'
    return response


class HealthLiveView(APIView):
    """Report that this application process is alive and can serve requests."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = ()

    def get(self, request):
        return _health_response({'status': 'ok', 'version': settings.APP_VERSION})


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
