import json
import logging
import re

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve

from apps.core.logging import SUCCESS_LEVEL, ColorJsonEventFormatter, JsonEventFormatter
from apps.core.middleware import REQUEST_ID_HEADER, RequestLoggingMiddleware


class ColorJsonEventFormatterTests(SimpleTestCase):
    def test_event_json_is_preserved_and_colored_by_level(self):
        formatter = ColorJsonEventFormatter()
        ansi = re.compile(r'\x1b\[[0-9;]*m')
        levels = (
            (logging.INFO, '\x1b[34m', 'INFO'),
            (logging.WARNING, '\x1b[33m', 'WARNING'),
            (logging.ERROR, '\x1b[31m', 'ERROR'),
            (SUCCESS_LEVEL, '\x1b[32m', 'SUCCESS'),
        )
        for level, color_code, level_name in levels:
            with self.subTest(level=level_name):
                record = logging.LogRecord(
                    'test.logger', level, __file__, 1, 'test.event', (), None
                )
                output = formatter.format(record)
                self.assertIn(color_code, output)
                payload = json.loads(ansi.sub('', output))
                self.assertEqual(payload['level'], level_name)
                self.assertEqual(payload['message'], 'test.event')


class RequestLoggingMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_request_summary_is_structured_and_excludes_query_and_secrets(self):
        request = self.factory.get(
            '/api/v1/gods/zeus/?search=private-query',
            HTTP_X_API_KEY='prefix.plaintextsecret',
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
