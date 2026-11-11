import re

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse

from website.tests import LandingHTML


def directives(response):
    return {
        parts[0]: parts[1:]
        for directive in response['Content-Security-Policy-Report-Only'].split('; ')
        if (parts := directive.split())
    }


class ContentSecurityPolicyTests(SimpleTestCase):
    def test_public_pages_and_admin_receive_report_only_not_enforcement(self):
        for route in ('website:home', 'swagger-ui', 'redoc', 'admin:login', 'api-directory'):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)
                self.assertNotIn('Content-Security-Policy', response)
                policy = directives(response)
                for name in ('object-src', 'frame-ancestors'):
                    self.assertEqual(policy[name], ["'none'"])
                for name in ('base-uri', 'form-action', 'connect-src'):
                    self.assertEqual(policy[name], ["'self'"])
                self.assertNotIn("'unsafe-inline'", policy['script-src'])
                self.assertNotIn("'unsafe-eval'", policy['script-src'])
                self.assertNotIn('report-uri', policy)
                self.assertNotIn('report-to', policy)

    def test_swagger_nonce_matches_header_changes_each_request_and_is_not_cached(self):
        nonces = []
        for _ in range(2):
            response = self.client.get(reverse('swagger-ui'))
            page = LandingHTML(response.content.decode())
            inline_scripts = [
                attrs for tag, attrs in page.elements if tag == 'script' and 'src' not in attrs
            ]
            self.assertEqual(len(inline_scripts), 1)
            nonce = inline_scripts[0]['nonce']
            self.assertRegex(nonce, r'^[A-Za-z0-9_-]{22}$')
            self.assertIn(f"'nonce-{nonce}'", directives(response)['script-src'])
            self.assertIn(
                '{% include template_name_js %}',
                (settings.BASE_DIR / 'website/templates/website/swagger_ui.html').read_text(),
            )
            self.assertIn('no-store', response['Cache-Control'])
            self.assertIn('private', response['Cache-Control'])
            nonces.append(nonce)
        self.assertNotEqual(*nonces)

    def test_redoc_exceptions_are_isolated_and_official_template_is_preserved(self):
        response = self.client.get(reverse('redoc'))
        self.assertTemplateUsed(response, 'drf_spectacular/redoc.html')
        self.assertEqual(
            response.data['redoc_standalone'],
            'https://cdn.jsdelivr.net/npm/redoc@2.5.2/bundles/redoc.standalone.js',
        )
        policy = directives(response)
        self.assertIn('https://cdn.jsdelivr.net', policy['script-src'])
        self.assertIn('https://fonts.googleapis.com', policy['style-src'])
        self.assertIn('https://fonts.gstatic.com', policy['font-src'])
        self.assertIn('blob:', policy['worker-src'])
        self.assertIn('https://cdn.redoc.ly', policy['img-src'])
        for route in ('website:home', 'swagger-ui', 'admin:login'):
            response = self.client.get(reverse(route))
            self.assertNotRegex(
                response['Content-Security-Policy-Report-Only'],
                r'jsdelivr|googleapis|gstatic|redoc\.ly|blob:',
            )
            self.assertEqual(directives(response)['font-src'], ["'self'"])

    def test_admin_nonce_tags_use_the_same_middleware_nonce(self):
        response = self.client.get(reverse('admin:login'))
        html = response.content.decode()
        nonces = set(re.findall(r'nonce="([A-Za-z0-9_-]+)"', html))
        self.assertEqual(len(nonces), 1)
        self.assertIn(f"'nonce-{nonces.pop()}'", directives(response)['script-src'])
