from xml.etree import ElementTree

from django.contrib.staticfiles import finders
from django.template import engines
from django.test import SimpleTestCase
from django.urls import resolve, reverse

from website.views import home


class HomeViewTests(SimpleTestCase):
    def test_home_is_public_and_uses_shared_layout_without_database_access(self):
        response = self.client.get(reverse('website:home'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'website/home.html')
        self.assertTemplateUsed(response, 'website/base.html')
        self.assertContains(response, '<title>Percy Jackson Fandom API</title>')
        self.assertContains(response, 'css/dist/styles.css')
        self.assertContains(response, 'Django + Tailwind = ❤️')
        self.assertContains(response, '<svg')
        self.assertContains(response, 'aria-hidden="true"')
        self.assertNotContains(response, '<c-icons.')
        self.assertEqual(reverse('website:home'), '/')
        self.assertIs(resolve('/').func, home)

    def test_home_supports_head_requests(self):
        response = self.client.head(reverse('website:home'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')


class LucideIconTests(SimpleTestCase):
    def render_icon(self, name, attributes='', context=None):
        # In-memory templates bypass Cotton's file loader, so use its equivalent DTL tag.
        template = engines['django'].from_string(
            '{% cotton icons.' + name + ' ' + attributes + ' /%}'
        )
        return ElementTree.fromstring(template.render(context or {}))

    def test_all_vendored_icons_render_as_decorative_inline_svg_by_default(self):
        for name in (
            'arrow-right',
            'book-open',
            'code',
            'copy',
            'external-link',
            'menu',
            'search',
            'x',
        ):
            with self.subTest(icon=name):
                svg = self.render_icon(name)
                self.assertEqual(svg.tag, '{http://www.w3.org/2000/svg}svg')
                self.assertEqual(svg.attrib['width'], '24')
                self.assertEqual(svg.attrib['height'], '24')
                self.assertEqual(svg.attrib['stroke'], 'currentColor')
                self.assertEqual(svg.attrib['stroke-width'], '2')
                self.assertEqual(svg.attrib['aria-hidden'], 'true')
                self.assertEqual(svg.attrib['focusable'], 'false')
                self.assertNotIn('role', svg.attrib)
                self.assertNotIn('aria-label', svg.attrib)
                self.assertTrue(len(svg))

    def test_attributes_and_accessible_label_pass_through_shared_base(self):
        svg = self.render_icon(
            'arrow-right',
            'size="18" stroke-width="1.5" class="text-teal-300" '
            'label="Continue" data-testid="next-icon"',
        )

        self.assertEqual(svg.attrib['width'], '18')
        self.assertEqual(svg.attrib['height'], '18')
        self.assertEqual(svg.attrib['stroke-width'], '1.5')
        self.assertIn('text-teal-300', svg.attrib['class'].split())
        self.assertEqual(svg.attrib['role'], 'img')
        self.assertEqual(svg.attrib['aria-label'], 'Continue')
        self.assertEqual(svg.attrib['data-testid'], 'next-icon')
        self.assertNotIn('aria-hidden', svg.attrib)
        self.assertNotIn('label', svg.attrib)
        self.assertNotIn('size', svg.attrib)

    def test_dynamic_labels_are_html_escaped(self):
        label = '"><script>alert("unsafe")</script>'
        svg = self.render_icon('search', ':label="label"', {'label': label})

        self.assertEqual(svg.attrib['aria-label'], label)
        self.assertIsNone(svg.find('.//script'))

    def test_upstream_license_is_available_to_collectstatic(self):
        self.assertIsNotNone(finders.find('vendor/lucide/LICENSE.txt'))
