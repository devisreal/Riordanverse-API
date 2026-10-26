import json

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve

from apps.core.logging import JsonEventFormatter
from apps.core.middleware import REQUEST_ID_HEADER, RequestLoggingMiddleware


class RequestLoggingMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_request_summary_is_structured_and_excludes_query_and_secrets(self):
        request = self.factory.get(
            '/api/v1/gods/zeus/?search=private-query',
            HTTP_API_KEY='prefix.plaintextsecret',
        )
        request.resolver_match = resolve('/api/v1/gods/zeus/')
        middleware = RequestLoggingMiddleware(lambda _request: HttpResponse(status=200))

        with self.assertLogs('api.request', level='INFO') as captured:
            response = middleware(request)

        self.assertRegex(response[REQUEST_ID_HEADER], r'^[0-9a-f]{32}$')
        record = captured.records[0]
        payload = json.loads(JsonEventFormatter().format(record))
        self.assertEqual(payload['event'], 'http.request.completed')
        self.assertEqual(payload['request_id'], response[REQUEST_ID_HEADER])
        self.assertEqual(payload['method'], 'GET')
        self.assertEqual(payload['route'], 'api/v1/gods/<slug:slug>/')
        self.assertEqual(payload['status_code'], 200)
        self.assertGreaterEqual(payload['duration_ms'], 0)
        self.assertNotIn('private-query', json.dumps(payload))
        self.assertNotIn('plaintextsecret', json.dumps(payload))

    def test_unauthorized_response_emits_security_event(self):
        request = self.factory.get('/api/v1/gods/zeus/')
        request.resolver_match = resolve('/api/v1/gods/zeus/')
        middleware = RequestLoggingMiddleware(lambda _request: HttpResponse(status=403))

        with self.assertLogs('api.security', level='WARNING') as captured:
            middleware(request)

        payload = json.loads(JsonEventFormatter().format(captured.records[0]))
        self.assertEqual(payload['event'], 'security.request_denied')
        self.assertEqual(payload['status_code'], 403)
        self.assertEqual(payload['route'], 'api/v1/gods/<slug:slug>/')

    def test_throttled_response_emits_security_event(self):
        request = self.factory.get('/api/v1/gods/zeus/')
        request.resolver_match = resolve('/api/v1/gods/zeus/')
        middleware = RequestLoggingMiddleware(lambda _request: HttpResponse(status=429))

        with self.assertLogs('api.security', level='WARNING') as captured:
            middleware(request)

        payload = json.loads(JsonEventFormatter().format(captured.records[0]))
        self.assertEqual(payload['event'], 'security.request_throttled')
        self.assertEqual(payload['status_code'], 429)
