import json
import posixpath
import re
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.test import RequestFactory, SimpleTestCase
from django.urls import get_script_prefix, resolve, reverse, set_script_prefix
from rest_framework.views import APIView

from apps.core.permissions import CachedHasAPIKey
from apps.core.views import API_DIRECTORY_ROUTES
from website.tests import LandingHTML


class SwaggerViewTests(SimpleTestCase):
    # No databases are enabled: documentation must render without querying one.
    def page(self):
        response = self.client.get(reverse('swagger-ui'))
        self.assertEqual(response.status_code, 200)
        return response, LandingHTML(response.content.decode())

    def test_swagger_is_public_html_using_the_custom_template_and_official_initializer(self):
        response, _ = self.page()
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'website/swagger_ui.html')
        self.assertTemplateUsed(response, 'drf_spectacular/swagger_ui.js')
        self.assertEqual(response.data['template_name_js'], 'drf_spectacular/swagger_ui.js')
        self.assertEqual(response.data['schema_url'], reverse('schema'))

    def test_navigation_heading_skip_link_and_shared_theme_control_are_accessible(self):
        response, page = self.page()
        headings = [attrs for tag, attrs in page.elements if tag == 'h1']
        self.assertEqual(len(headings), 1)
        self.assertTrue(headings[0].get('id'))
        self.assertTrue(
            any(attrs.get('aria-labelledby') == headings[0]['id'] for _, attrs in page.elements)
        )
        mains = [attrs for tag, attrs in page.elements if tag == 'main']
        self.assertEqual(len(mains), 1)
        self.assertIn(f'#{mains[0]["id"]}', page.links)
        self.assertEqual(mains[0].get('tabindex'), '-1')
        self.assertIn('swagger-ui', page.ids)
        self.assertEqual(len(page.ids), len(set(page.ids)))
        for route in ('website:home', 'api-directory', 'redoc', 'schema'):
            with self.subTest(route=route):
                self.assertIn(reverse(route), page.links)
        self.assertTrue(any(tag == 'noscript' for tag, _ in page.elements))
        self.assertTemplateUsed(response, 'cotton/brand/mark.html')
        self.assertTemplateUsed(response, 'cotton/ui/theme_toggle.html')
        toggles = [attrs for _, attrs in page.elements if 'data-theme-toggle' in attrs]
        self.assertEqual(len(toggles), 1)
        self.assertEqual(toggles[0].get('type'), 'button')
        self.assertTrue(toggles[0].get('aria-label'))
        self.assertIn('hidden', toggles[0], 'Only reveal the control after theme.js binds it')

    def test_runtime_assets_are_local_and_exclude_the_landing_bundle(self):
        _, page = self.page()
        scripts = [
            attrs['src'] for tag, attrs in page.elements if tag == 'script' and 'src' in attrs
        ]
        self.assertEqual(
            scripts,
            [static('website/js/theme.js'), static('vendor/swagger-ui/dist/swagger-ui-bundle.js')],
        )
        styles = [
            attrs['href']
            for tag, attrs in page.elements
            if tag == 'link' and 'stylesheet' in attrs.get('rel', '').split()
        ]
        self.assertEqual(
            styles,
            [static('vendor/swagger-ui/dist/swagger-ui.css'), static('css/dist/styles.css')],
        )
        assets = []
        for tag, attrs in page.elements:
            if tag in ('script', 'img', 'source', 'iframe') and attrs.get('src'):
                assets.append(attrs['src'])
            elif tag == 'link' and attrs.get('href'):
                assets.append(attrs['href'])
        for url in assets:
            with self.subTest(asset=url):
                self.assertFalse(urlsplit(url).scheme or urlsplit(url).netloc, url)
                self.assertTrue(url.startswith(settings.STATIC_URL), url)
                self.assertIsNotNone(finders.find(url.removeprefix(settings.STATIC_URL)))

    def test_local_fonts_and_vendor_licenses_are_discoverable(self):
        css_path = finders.find('css/dist/styles.css')
        self.assertIsNotNone(css_path)
        css = Path(css_path).read_text()
        package = json.loads((settings.BASE_DIR / 'website/static_src/package.json').read_text())
        self.assertIs(package['scarfSettings']['enabled'], False)
        self.assertIn('.swagger-ui', css, 'Swagger descendant utilities must be compiled')
        self.assertIsNone(finders.find('website/css/swagger.css'))
        references = set()
        for match in re.finditer(r'url\(\s*[\'"]?([^\s)\'"]+)', css):
            url = match[1]
            self.assertFalse(urlsplit(url).scheme or url.startswith('//'), url)
            path = posixpath.normpath(posixpath.join('css/dist', url))
            references.add(path)
            with self.subTest(css_asset=path):
                self.assertIsNotNone(finders.find(path))
        self.assertTrue(
            {
                'website/fonts/plus-jakarta-sans-latin-variable.woff2',
                'website/fonts/jetbrains-mono-latin-variable.woff2',
            }
            <= references
        )
        self.assertNotRegex(css.lower(), r'@import|fonts\.google|fonts\.gstatic')
        vendor_css = Path(finders.find('vendor/swagger-ui/dist/swagger-ui.css')).read_text()
        self.assertNotIn(
            'sourceMappingURL=', vendor_css, 'Omitted maps must not break collectstatic'
        )
        self.assertIn('@layer theme, base, swagger, components, utilities;', vendor_css)
        self.assertTemplateUsed(self.page()[0], 'cotton/swagger/panel.html')
        for path in (
            'website/fonts/plusjakartasans-LICENSE.txt',
            'website/fonts/jetbrainsmono-LICENSE.txt',
            'vendor/swagger-ui/dist/LICENSE',
            'vendor/swagger-ui/dist/NOTICE',
            'vendor/swagger-ui/dist/swagger-ui-bundle.js.LICENSE.txt',
        ):
            with self.subTest(license=path):
                self.assertIsNotNone(finders.find(path))

    def test_ui_settings_keep_schema_order_filtering_and_authorization_in_memory(self):
        response, _ = self.page()
        ui_settings = json.loads(response.data['settings'])
        self.assertIsNone(ui_settings['tagsSorter'])
        self.assertIs(ui_settings['filter'], True)
        self.assertIs(ui_settings['persistAuthorization'], False)
        self.assertIsNone(ui_settings['validatorUrl'])
        # Parse only the JSON declaration, never evaluate JavaScript.
        declaration = re.search(
            r'const\s+swaggerSettings\s*=\s*(\{.*?\})\s*;',
            response.content.decode(),
            re.DOTALL,
        )
        self.assertIsNotNone(declaration)
        self.assertEqual(json.loads(declaration[1]), ui_settings)

    def test_official_initializer_retains_interceptors_and_csrf_header(self):
        response, _ = self.page()
        html = response.content.decode()
        for name in ('requestInterceptor', 'responseInterceptor'):
            with self.subTest(interceptor=name):
                self.assertRegex(html, rf'const\s+{name}\s*=')
                self.assertRegex(html, rf'\b{name}\s*,')
        self.assertRegex(html, r'const\s+ui\s*=\s*SwaggerUIBundle\s*\(')
        self.assertIn('request.loadSpec', html)
        self.assertIn('request.credentials === "same-origin"', html)
        header = response.data['csrf_header_name']
        self.assertEqual(header, settings.CSRF_HEADER_NAME.removeprefix('HTTP_').replace('_', '-'))
        self.assertRegex(html, rf'request\.headers\["{re.escape(header)}"\]\s*=\s*"[A-Za-z0-9]+"')
        self.assertNotIn('{{ csrf_token }}', html)
        self.assertTrue(response.cookies['csrftoken'].value)

    def test_reversed_schema_and_navigation_urls_honor_script_prefix(self):
        original_prefix = get_script_prefix()
        try:
            set_script_prefix('/archive/')
            view = resolve('/api/docs/').func
            response = view(RequestFactory().get('/api/docs/'))
            response.render()
            page = LandingHTML(response.content.decode())
            self.assertEqual(response.data['schema_url'], reverse('schema'))
            self.assertEqual(response.data['schema_url'], '/archive/api/schema/')
            for route in ('website:home', 'api-directory', 'redoc', 'schema'):
                with self.subTest(route=route):
                    self.assertIn(reverse(route), page.links)
        finally:
            set_script_prefix(original_prefix)

    def test_redoc_remains_official_and_other_pages_do_not_load_swagger_styles(self):
        response = self.client.get(reverse('redoc'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'drf_spectacular/redoc.html')
        self.assertTemplateNotUsed(response, 'website/swagger_ui.html')
        self.assertEqual(response.data['schema_url'], reverse('schema'))
        self.assertTrue(
            any(tag == 'redoc' for tag, _ in LandingHTML(response.content.decode()).elements)
        )
        for route in ('redoc', 'website:home', 'admin:login'):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, static('vendor/swagger-ui/dist/swagger-ui.css'))


class SwaggerAPIContractTests(SimpleTestCase):
    def test_public_directory_and_protected_books_contracts_remain_unchanged(self):
        # The test settings otherwise relax APIView's default permissions.
        with patch.object(APIView, 'permission_classes', [CachedHasAPIKey]):
            directory = self.client.get(reverse('api-directory'))
            books = self.client.get(reverse('book-list'))
        self.assertEqual(directory.status_code, 200)
        self.assertEqual(directory['Content-Type'], 'application/json')
        self.assertEqual(
            directory.json(),
            {name: reverse(route) for name, route in API_DIRECTORY_ROUTES.items()},
        )
        self.assertEqual(books.status_code, 403)
        self.assertEqual(books.json()['error']['code'], 'FORBIDDEN')

    def test_real_public_schema_keeps_api_key_security_and_directory_paths(self):
        with patch.object(APIView, 'permission_classes', [CachedHasAPIKey]):
            response = self.client.get(reverse('schema'), {'format': 'json'})
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        scheme = schema['components']['securitySchemes']['ApiKeyAuth']
        self.assertEqual(scheme['type'], 'apiKey')
        self.assertEqual(scheme['in'], 'header')
        self.assertEqual(scheme['name'], 'X-API-Key')
        self.assertEqual(
            schema['paths'][reverse('book-list')]['get']['security'], [{'ApiKeyAuth': []}]
        )
        directory = schema['paths'][reverse('api-directory')]['get']
        self.assertEqual(directory.get('security', []), [])
        self.assertEqual(directory['tags'], ['API Directory'])
        self.assertEqual(set(directory['responses']['200']['content']), {'application/json'})
        directory_schema = schema['components']['schemas']['APIDirectory']
        self.assertEqual(set(directory_schema['properties']), set(API_DIRECTORY_ROUTES))
        for name, route in API_DIRECTORY_ROUTES.items():
            with self.subTest(collection=name):
                self.assertIn(reverse(route), schema['paths'])
