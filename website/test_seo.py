import json
import re
from unittest.mock import patch
from xml.etree.ElementTree import fromstring

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve, reverse

from website.seo import (
    GUIDE_TITLE,
    HOME_TITLE,
    SearchIndexingMiddleware,
    metadata,
    public_url,
    structured_data,
)


@override_settings(SEO_PUBLIC_ORIGIN='https://riordanverse.cc', SEO_INDEXING_ENABLED=True)
class SearchDiscoveryTests(SimpleTestCase):
    def test_robots_and_sitemap_are_public_and_list_selected_indexable_pages(self):
        robots = self.client.get(reverse('website:robots'))
        self.assertEqual(robots.status_code, 200)
        self.assertIn('text/plain', robots['Content-Type'])
        self.assertEqual(
            robots.content.decode(),
            'User-agent: *\nAllow: /\n\nSitemap: https://riordanverse.cc/sitemap.xml\n',
        )
        response = self.client.get(reverse('website:sitemap'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/xml', response['Content-Type'])
        root = fromstring(response.content)
        self.assertEqual(root.tag, '{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
        self.assertEqual(
            [
                element.text
                for element in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            ],
            [
                'https://riordanverse.cc/',
                'https://riordanverse.cc/getting-started/',
                'https://riordanverse.cc/api/docs/',
                'https://riordanverse.cc/api/redoc/',
            ],
        )
        self.assertNotIn(b'lastmod', response.content)
        for route in ('website:robots', 'website:sitemap'):
            self.assertNotIn('X-Robots-Tag', self.client.get(reverse(route)))
            head = self.client.head(reverse(route))
            self.assertEqual(head.status_code, 200)
            self.assertNotIn('X-Robots-Tag', head)
            rejected = self.client.post(reverse(route))
            self.assertEqual(rejected.status_code, 405)
            self.assertEqual(rejected['X-Robots-Tag'], 'noindex, nofollow')

    def test_selected_public_pages_are_indexable_but_other_routes_are_not(self):
        for route in ('website:home', 'website:getting-started', 'swagger-ui', 'redoc'):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)
                self.assertNotIn('X-Robots-Tag', response)
        for url in (
            '/api/v1/',
            '/health/live/',
            '/admin/login/',
            '/missing-seo-route/',
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow')
        middleware = SearchIndexingMiddleware(lambda request: HttpResponse())
        for url in ('/api/v1/creatures/', '/auth/request-key/'):
            with self.subTest(url=url):
                request = RequestFactory().get(url)
                request.resolver_match = resolve(url)
                response = middleware(request)
                self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow')
        response = self.client.get(reverse('website:home'), HTTP_HOST='testserver')
        self.assertContains(response, 'rel="canonical" href="https://riordanverse.cc/"')

    @override_settings(SEO_INDEXING_ENABLED=False)
    def test_staging_and_local_pages_are_not_indexable_or_advertised(self):
        self.assertEqual(self.client.get('/robots.txt').content, b'User-agent: *\nAllow: /\n')
        self.assertEqual(len(fromstring(self.client.get('/sitemap.xml').content)), 0)
        for url in ('/robots.txt', '/sitemap.xml'):
            self.assertNotIn('X-Robots-Tag', self.client.get(url))
        for route in ('website:home', 'website:getting-started', 'swagger-ui', 'redoc'):
            response = self.client.get(reverse(route))
            self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow')

    def test_guide_is_rendered_without_database_or_live_api_requests(self):
        # SimpleTestCase forbids DB access; outbound calls must not be needed either.
        with patch('requests.sessions.Session.request', side_effect=AssertionError('No network')):
            response = self.client.get('/getting-started/?utm_source=example')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'<title>{GUIDE_TITLE.replace("&", "&amp;")}</title>')
        for text in (
            'X-API-Key',
            'consumer_name',
            'divine_parent',
            'total_pages',
            '$API_KEY',
            'Unofficial project',
            'site.js',
        ):
            self.assertContains(response, text)
        self.assertNotContains(response, 'utm_source')
        self.assertContains(self.client.get('/'), 'href="/getting-started/"', count=2)

    def test_guide_rate_limits_follow_resources_before_key_requests(self):
        response = self.client.get(reverse('website:getting-started'))
        html = response.content.decode()
        self.assertLess(html.index('id="resources"'), html.index('id="rate-limiting"'))
        self.assertLess(html.index('id="rate-limiting"'), html.index('id="quick-start"'))
        for text in (
            '1,000 requests per hour per API key',
            '5 requests per hour per client IP address',
            'Key revocation shares this quota.',
            '429 Too Many Requests',
            'Retry-After',
            'RateLimit-Limit',
            'RateLimit-Remaining',
            'RateLimit-Reset',
        ):
            self.assertContains(response, text)

    def test_json_ld_has_real_identity_distinct_titles_and_csp_nonce(self):
        for url, title in (('/', HOME_TITLE), ('/getting-started/', GUIDE_TITLE)):
            response = self.client.get(url)
            match = re.search(
                r'<script type="application/ld\+json" nonce="([^"]+)">(.*?)</script>',
                response.content.decode(),
                re.DOTALL,
            )
            self.assertIsNotNone(match)
            self.assertIn(f"'nonce-{match[1]}'", response['Content-Security-Policy-Report-Only'])
            graph = json.loads(match[2])['@graph']
            self.assertEqual(graph[0]['name'], 'Riordanverse API')
            self.assertEqual(graph[1]['@type'], 'WebAPI')
            self.assertEqual(graph[2]['name'], title)
            self.assertEqual(graph[2]['url'], 'https://riordanverse.cc' + url)
            self.assertEqual(any(item['@type'] == 'BreadcrumbList' for item in graph), url != '/')
            self.assertFalse(any('aggregateRating' in item or 'license' in item for item in graph))

    def test_json_ld_escapes_script_termination(self):
        request = RequestFactory().get('/')
        social = metadata(request)
        value = structured_data(
            request, social, 'https://example.org/</script><script>alert(1)</script>&'
        )
        self.assertNotIn('<', value)
        self.assertNotIn('>', value)
        self.assertNotIn('&', value)
        self.assertIn('</script>', json.loads(value)['@graph'][0]['sameAs'][0])

    def test_public_origin_validation_and_external_static_url(self):
        request = RequestFactory().get('/')
        self.assertEqual(
            public_url(request, '/getting-started/'), 'https://riordanverse.cc/getting-started/'
        )
        self.assertEqual(
            public_url(request, 'https://cdn.example/card.png'), 'https://cdn.example/card.png'
        )
        for origin in (
            'https://example.org/path',
            'https://user:pass@example.org',
            'https://example.org?x=1',
            'javascript:alert(1)',
        ):
            with (
                self.subTest(origin=origin),
                override_settings(SEO_PUBLIC_ORIGIN=origin),
                self.assertRaises(ImproperlyConfigured),
            ):
                public_url(request, '/')
