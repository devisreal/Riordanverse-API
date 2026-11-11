import struct
from pathlib import Path

from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import get_script_prefix, reverse, set_script_prefix

from website.tests import LandingHTML
from website.views import home


class SocialMetadataTests(SimpleTestCase):
    def metadata(self, response):
        page = LandingHTML(response.content.decode())
        metadata = {}
        for tag, attrs in page.elements:
            if tag == 'meta' and (key := attrs.get('property', attrs.get('name'))):
                self.assertNotIn(key, metadata, f'Duplicate metadata: {key}')
                metadata[key] = attrs.get('content')
        canonicals = [
            attrs['href']
            for tag, attrs in page.elements
            if tag == 'link' and attrs.get('rel') == 'canonical'
        ]
        self.assertEqual(canonicals, [metadata['og:url']])
        return metadata

    def test_metadata_is_server_rendered_consistent_and_query_free(self):
        response = self.client.get(reverse('website:home'), {'utm_source': 'example'})
        self.assertEqual(response.status_code, 200)
        metadata = self.metadata(response)
        self.assertEqual(metadata['og:type'], 'website')
        self.assertEqual(metadata['og:title'], 'Percy Jackson Fandom API')
        self.assertEqual(metadata['og:site_name'], metadata['og:title'])
        self.assertEqual(metadata['twitter:title'], metadata['og:title'])
        self.assertEqual(metadata['description'], metadata['og:description'])
        self.assertEqual(metadata['twitter:description'], metadata['og:description'])
        self.assertEqual(metadata['og:url'], 'http://testserver/')
        self.assertEqual(metadata['twitter:card'], 'summary_large_image')
        self.assertEqual(metadata['twitter:image'], metadata['og:image'])
        self.assertEqual(metadata['twitter:image:alt'], metadata['og:image:alt'])
        self.assertIn('Unofficial fan project', metadata['og:image:alt'])
        self.assertEqual(metadata['og:image:type'], 'image/png')
        self.assertEqual((metadata['og:image:width'], metadata['og:image:height']), ('1200', '630'))
        self.assertEqual(
            metadata['og:image'],
            'http://testserver' + static('website/images/social-preview.png'),
        )
        self.assertNotIn('twitter:site', metadata, 'Do not invent a social account')

    @override_settings(ALLOWED_HOSTS=['archive.example'], STATIC_URL='/static/')
    def test_absolute_urls_follow_https_host_and_mounted_route_not_tracking_query(self):
        original_prefix = get_script_prefix()
        try:
            set_script_prefix('/archive/')
            request = RequestFactory().get(
                '/archive/?utm_source=tracking', secure=True, HTTP_HOST='archive.example'
            )
            metadata = self.metadata(home(request))
            self.assertEqual(metadata['og:url'], 'https://archive.example/archive/')
            self.assertEqual(
                metadata['og:image'],
                request.build_absolute_uri(static('website/images/social-preview.png')),
            )
        finally:
            set_script_prefix(original_prefix)

    def test_preview_png_is_available_at_declared_dimensions_with_editable_source(self):
        path = finders.find('website/images/social-preview.png')
        self.assertIsNotNone(path)
        png = Path(path).read_bytes()
        self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(png[12:16], b'IHDR')
        self.assertEqual(struct.unpack('>II', png[16:24]), (1200, 630))
        self.assertIsNotNone(finders.find('website/images/social-preview.svg'))
