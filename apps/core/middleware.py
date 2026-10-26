"""Request correlation and safe request/security event logging."""

import logging
import time
import uuid

request_logger = logging.getLogger('api.request')
security_logger = logging.getLogger('api.security')
REQUEST_ID_HEADER = 'X-Request-ID'


class RequestLoggingMiddleware:
    """Attach a request ID and log one summary without request data or secrets."""

    sync_capable = True
    async_capable = False

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = uuid.uuid4().hex
        request.request_id = request_id
        started_at = time.perf_counter()

        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        route_match = getattr(request, 'resolver_match', None)
        route = getattr(route_match, 'route', None) or 'unmatched'
        status_code = response.status_code
        fields = {
            'request_id': request_id,
            'method': request.method,
            'route': route,
            'status_code': status_code,
            'duration_ms': duration_ms,
        }

        request_logger.info(
            'http.request.completed',
            extra={'event': 'http.request.completed', **fields},
        )
        if status_code in (401, 403):
            security_logger.warning(
                'security.request_denied',
                extra={'event': 'security.request_denied', **fields},
            )
        elif status_code == 429:
            security_logger.warning(
                'security.request_throttled',
                extra={'event': 'security.request_throttled', **fields},
            )

        response[REQUEST_ID_HEADER] = request_id
        return response
