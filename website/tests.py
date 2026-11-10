import json
import posixpath
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template import engines
from django.templatetags.static import static
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import get_script_prefix, resolve, reverse, set_script_prefix

from apps.characters.serializers import CharacterDetailSerializer
from apps.core.views import API_DIRECTORY_ROUTES
from website.content import get_home_context
from website.views import home


class LandingHTML(HTMLParser):
    """Inspect rendered markup, not template spelling or syntax-highlight spans."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.ids = []
        self.text = []
        self.code = {}
        self._pre = None
        self._code_tag = None
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'pre' or (tag == 'code' and 'id' in attrs):
            self._pre = attrs.get('id')
            self._code_tag = tag
            self.code[self._pre] = ''

    def handle_endtag(self, tag):
        if tag == self._code_tag:
            self._pre = None
            self._code_tag = None

    def handle_data(self, data):
        self.text.append(data)
        if self._pre is not None:
            self.code[self._pre] += data

    @property
    def links(self):
        return [attrs['href'] for tag, attrs in self.elements if tag == 'a' and 'href' in attrs]


class HomeViewTests(SimpleTestCase):
    # SimpleTestCase deliberately prohibits database queries on every connection.
    def page(self, **extra):
        response = self.client.get(reverse('website:home'), **extra)
        self.assertEqual(response.status_code, 200)
        return response, LandingHTML(response.content.decode())

    def test_home_is_public_and_uses_shared_layout_without_database_access(self):
        response, page = self.page()
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'website/home.html')
        self.assertTemplateUsed(response, 'website/base.html')
        self.assertContains(response, '<title>Percy Jackson Fandom API</title>')
        text = ' '.join(' '.join(page.text).split())
        for heading in (
            'The Riordanverse,',
            'ready to build with.',
            'Curated Archives',
            'Structured Lore Architecture',
            'Engineered for Mythic Scale',
            'Quick Start in 3 Steps',
            'Specs & Tooling',
            'People & Divinities',
            'Stories & Narrative',
            'Places & Factions',
            'Bestiary & Regalia',
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, text)
        for section in ('main-content', 'resources', 'features', 'quick-start'):
            self.assertIn(section, page.ids)
        self.assertContains(response, '<svg')
        self.assertContains(response, 'aria-hidden="true"')
        self.assertEqual(reverse('website:home'), '/')
        self.assertIs(resolve('/').func, home)

    def test_theme_controls_are_accessible_and_hidden_until_javascript_binds(self):
        response, page = self.page()
        toggles = [attrs for tag, attrs in page.elements if 'data-theme-toggle' in attrs]
        self.assertEqual(len(toggles), 1)
        self.assertEqual(toggles[0]['type'], 'button')
        self.assertTrue(toggles[0]['aria-label'])
        self.assertIn('hidden', toggles[0])
        options = [attrs for _, attrs in page.elements if 'data-theme-options' in attrs]
        self.assertEqual(len(options), 1)
        self.assertIn('hidden', options[0])
        choices = [attrs for _, attrs in page.elements if 'data-theme-choice' in attrs]
        self.assertEqual({attrs['data-theme-choice'] for attrs in choices}, {'light', 'dark'})
        for choice in choices:
            self.assertEqual(choice['type'], 'button')
            self.assertEqual(choice['aria-pressed'], 'false')
        self.assertEqual(
            {attrs['data-theme-icon'] for _, attrs in page.elements if 'data-theme-icon' in attrs},
            {'light', 'dark'},
        )
        for _, attrs in page.elements:
            if 'data-theme-icon' in attrs:
                # Avoid inline SVG baseline/line-height shifting the icon vertically.
                self.assertTrue(
                    {'flex', 'items-center', 'justify-center'} <= set(attrs['class'].split())
                )
        html = response.content.decode()
        # Resolve the stored preference before loading CSS, not after the first paint.
        self.assertLess(
            html.index(static('website/js/theme.js')), html.index(static('css/dist/styles.css'))
        )
        self.assertNotRegex(html, r'\son\w+=')

    def test_tablet_explorer_keeps_real_destination_and_compact_copy(self):
        response, _ = self.page()
        header = response.content.decode().split('</header>', 1)[0]
        self.assertIn('Explore API</span>', header)
        self.assertIn('Explore the API</span>', header)
        self.assertIn(f'href="{reverse("api-directory")}"', header)

    def test_home_supports_public_head_requests(self):
        response = self.client.head(reverse('website:home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        self.assertEqual(response.content, b'')

    def test_render_does_not_call_api_or_network(self):
        with (
            patch('apps.core.views.APIDirectoryView.get', side_effect=AssertionError('API call')),
            patch('requests.sessions.Session.request', side_effect=AssertionError('HTTP call')),
            patch('urllib.request.urlopen', side_effect=AssertionError('HTTP call')),
            patch('socket.create_connection', side_effect=AssertionError('Network call')),
        ):
            self.page()
            self.assertEqual(self.client.head(reverse('website:home')).status_code, 200)

    def test_document_has_unique_ids_and_valid_internal_references(self):
        response, page = self.page()
        self.assertEqual([key for key, count in Counter(page.ids).items() if count > 1], [])
        for tag, attrs in page.elements:
            with self.subTest(tag=tag, attrs=attrs):
                self.assertFalse(tag.startswith('c-'), 'Unresolved Cotton component')
                for attribute in ('aria-controls', 'aria-labelledby', 'aria-describedby'):
                    for target in attrs.get(attribute, '').split():
                        self.assertIn(target, page.ids)
                for attribute in ('data-copy-target', 'data-tab'):
                    if attrs.get(attribute):
                        self.assertIn(attrs[attribute].removeprefix('#'), page.ids)
        for href in page.links:
            parsed = urlsplit(href)
            with self.subTest(href=href):
                if not parsed.netloc and not parsed.scheme:
                    if parsed.path:
                        resolve(parsed.path)
                    if parsed.fragment:
                        self.assertIn(unquote(parsed.fragment), page.ids)
                else:
                    self.assertEqual(parsed.scheme, 'https')
                    self.assertIn(
                        parsed.netloc,
                        (
                            'github.com',
                            'riordan.fandom.com',
                            'visitolympus.travel',
                            'commons.wikimedia.org',
                            'creativecommons.org',
                        ),
                    )
        self.assertNotRegex(response.content.decode(), r'<c-|\{%|\{\{')

    def test_document_links_to_real_documentation_and_repository(self):
        _, page = self.page()
        for name in ('api-directory', 'swagger-ui', 'redoc', 'schema'):
            with self.subTest(route=name):
                self.assertIn(reverse(name), page.links)
        self.assertIn('https://github.com/devisreal/Percy-Jackson-Fandom-API', page.links)

    def test_external_links_open_safely_in_new_tabs_and_internal_navigation_does_not(self):
        _, page = self.page()
        external_count = 0
        for tag, attrs in page.elements:
            if tag != 'a':
                continue
            href = attrs.get('href', '')
            destination = urlsplit(urljoin('http://testserver/', href))
            with self.subTest(href=href):
                if destination.netloc != 'testserver':
                    external_count += 1
                    self.assertEqual(attrs.get('target'), '_blank')
                    self.assertTrue({'noopener', 'noreferrer'} <= set(attrs.get('rel', '').split()))
                elif 'example-health' in attrs.get('class', '').split():
                    self.assertEqual(href, reverse('health-live'))
                    self.assertEqual(attrs.get('target'), '_blank')
                    self.assertTrue({'noopener', 'noreferrer'} <= set(attrs.get('rel', '').split()))
                else:
                    self.assertNotEqual(attrs.get('target'), '_blank')
        self.assertGreater(external_count, 0)

    def test_example_header_health_links_and_timing_remain_illustrative(self):
        response, page = self.page()
        health_links = [
            attrs
            for tag, attrs in page.elements
            if tag == 'a' and 'example-health' in attrs.get('class', '').split()
        ]
        self.assertEqual(len(health_links), 2)
        for attrs in health_links:
            self.assertEqual(attrs['href'], reverse('health-live'))
            self.assertIn('illustrative, not live measurements', attrs['title'])
        self.assertContains(response, 'Health: Operational', count=2)
        self.assertContains(response, 'STATUS 200', count=1)
        self.assertContains(response, '18.4ms', count=1)
        self.assertContains(response, 'Static example · not live')
        self.assertNotContains(response, 'api.pjo.archive.org')

    def test_footer_specifications_have_list_items_and_a_separate_source_link(self):
        response, page = self.page()
        specification_list = re.search(
            r'<ul class="footer-specifications(?:\s[^"]*)?">(.*?)</ul>',
            response.content.decode(),
            re.DOTALL,
        )
        self.assertIsNotNone(specification_list)
        specifications = LandingHTML(specification_list.group(1))
        self.assertEqual(sum(tag == 'li' for tag, _ in specifications.elements), 3)
        self.assertEqual(
            specifications.links,
            [reverse('swagger-ui'), reverse('redoc'), reverse('schema')],
        )
        source_links = [
            attrs
            for tag, attrs in page.elements
            if tag == 'a' and 'footer-source' in attrs.get('class', '').split()
        ]
        self.assertEqual(len(source_links), 1)
        self.assertEqual(source_links[0]['href'], 'https://riordan.fandom.com/wiki/Riordan_Wiki')
        self.assertNotIn('brand', source_links[0].get('class', '').split())
        for tag, attrs in page.elements:
            if tag == 'a' and 'brand' in attrs.get('class', '').split():
                self.assertNotIn('footer-source', attrs['class'].split())

    def test_hero_description_has_a_scoped_theme_color(self):
        _, page = self.page()
        descriptions = [
            attrs
            for tag, attrs in page.elements
            if tag == 'p' and 'hero-description' in attrs.get('class', '').split()
        ]
        self.assertEqual(len(descriptions), 1)
        self.assertIn('text-hero-description', descriptions[0]['class'].split())
        self.assertIn('text-shadow-(--hero-description-shadow)', descriptions[0]['class'].split())

    def test_every_api_directory_collection_has_a_matching_link(self):
        _, page = self.page()
        linked_paths = {urlsplit(href).path for href in page.links}
        # Import the directory's route map, rather than making an API request.
        for collection, route in API_DIRECTORY_ROUTES.items():
            with self.subTest(collection=collection):
                self.assertIn(reverse(route), linked_paths)

    def test_utility_example_links_match_displayed_queries(self):
        _, page = self.page()
        for code_id, route, query in (
            ('search-endpoint', 'search', 'q=percy'),
            ('images-endpoint', 'image-list', 'source_type=wiki'),
        ):
            with self.subTest(example=code_id):
                url = f'{reverse(route)}?{query}'
                self.assertIn(url, page.links)
                self.assertEqual(page.code[code_id].strip(), f'GET {url}')

    def test_code_snippets_do_not_include_template_indentation(self):
        _, page = self.page()
        context = get_home_context(RequestFactory().get('/'))
        for code_id, key in (
            ('request-code', 'request_raw'),
            ('response-code', 'response_json'),
            ('key-request-code', 'request_key_raw'),
            ('curl-code', 'curl_raw'),
        ):
            with self.subTest(snippet=code_id):
                self.assertEqual(page.code[code_id].rstrip('\n'), context[key].rstrip('\n'))

    def test_lore_images_are_the_three_local_archives(self):
        _, page = self.page()
        images = [attrs for tag, attrs in page.elements if tag == 'img']
        expected = {
            'website/images/lore-camp.webp',
            'website/images/lore-olympus.webp',
            'website/images/lore-trident.webp',
        }
        self.assertEqual({image['src'] for image in images}, {static(path) for path in expected})
        self.assertEqual(len(images), 3)
        context = get_home_context(RequestFactory().get('/'))
        for image, item in zip(images, context['lore_cards'], strict=True):
            self.assertEqual(image['alt'], item['image_alt'])
            self.assertEqual(int(image['width']), item['image_width'])
            self.assertEqual(int(image['height']), item['image_height'])
            self.assertEqual(image['loading'], 'lazy')
        for path in expected:
            with self.subTest(path=path):
                asset = finders.find(path)
                self.assertIsNotNone(asset)
                self.assertEqual(Path(asset).read_bytes()[8:12], b'WEBP')

    def test_lore_image_credits_are_visible_and_link_to_sources_and_trident_license(self):
        response, _ = self.page()
        credits = re.findall(
            r'<p class="lore-image-credit(?:\s[^"]*)?">(.*?)</p>',
            response.content.decode(),
            re.DOTALL,
        )
        self.assertEqual(len(credits), 3)
        context = get_home_context(RequestFactory().get('/'))
        for credit, item in zip(credits, context['lore_cards'], strict=True):
            with self.subTest(image=item['image']):
                parsed = LandingHTML(credit)
                self.assertIn(item['image_credit'], ''.join(parsed.text))
                self.assertIn(item['image_source_url'], parsed.links)
                self.assertNotIn('hidden', credit)
                for tag, attrs in parsed.elements:
                    if tag == 'a':
                        self.assertEqual(attrs['target'], '_blank')
                        self.assertTrue({'noopener', 'noreferrer'} <= set(attrs['rel'].split()))
        self.assertIn('Cropped photo:', credits[2])
        self.assertIn('Oceancetaceen', credits[2])
        self.assertIn('CC BY-SA 3.0', credits[2])
        self.assertIn('https://creativecommons.org/licenses/by-sa/3.0/', credits[2])

    def test_runtime_styles_scripts_fonts_and_backgrounds_are_local_and_discoverable(self):
        _, page = self.page()
        assets = []
        for tag, attrs in page.elements:
            if tag == 'script':
                self.assertTrue(attrs.get('src'), 'Scripts must be external local static files')
                assets.append(attrs['src'])
            elif tag in ('link', 'img', 'source', 'iframe'):
                if attrs.get('href') or attrs.get('src'):
                    assets.append(attrs.get('href') or attrs['src'])
        self.assertIn(static('css/dist/styles.css'), assets)
        self.assertIn(static('website/js/theme.js'), assets)
        self.assertIn(static('website/js/site.js'), assets)
        self.assertIn(static('website/js/dist/animations.js'), assets)
        self.assertIsNotNone(finders.find('vendor/motion/LICENSE.txt'))
        for url in assets:
            with self.subTest(asset=url):
                self.assertTrue(url.startswith(settings.STATIC_URL), url)
                self.assertFalse(urlsplit(url).netloc, url)
                self.assertIsNotNone(finders.find(url.removeprefix(settings.STATIC_URL)))
        css_path = finders.find('css/dist/styles.css')
        self.assertIsNotNone(css_path)
        css = Path(css_path).read_text()
        expected = {
            'website/fonts/plus-jakarta-sans-latin-variable.woff2',
            'website/fonts/jetbrains-mono-latin-variable.woff2',
            'website/images/background-light.webp',
            'website/images/background-dark.webp',
        }
        references = set()
        for match in re.finditer(r'url\(\s*[\'"]?([^\s)\'"]+)', css):
            url = match[1]
            self.assertFalse(urlsplit(url).scheme or url.startswith('//'), url)
            path = posixpath.normpath(posixpath.join('css/dist', url))
            references.add(path)
            with self.subTest(css_asset=path):
                self.assertIsNotNone(finders.find(path))
        self.assertTrue(expected <= references, expected - references)
        for theme in ('light', 'dark'):
            original = f'website/images/background-{theme}.jpg'
            self.assertIsNotNone(finders.find(original), 'Keep original JPEG backgrounds')
            self.assertNotIn(original, references)
        self.assertNotRegex(css.lower(), r'@import|fonts\.google|material.symbols|material.icons')

    def test_reveal_targets_remain_visible_without_the_animation_script(self):
        _, page = self.page()
        groups = [
            attrs['data-reveal-group'] for _, attrs in page.elements if 'data-reveal-group' in attrs
        ]
        self.assertEqual(Counter(groups), {'hero': 1, 'scroll': 5})
        grids = [attrs for _, attrs in page.elements if 'data-reveal-stagger' in attrs]
        self.assertEqual(len(grids), 7, 'Every card grid, including overview stats, must stagger')
        self.assertTrue(
            all('data-reveal' not in attrs for attrs in grids),
            'Do not animate both grids and their cards',
        )
        targets = [attrs for _, attrs in page.elements if 'data-reveal' in attrs]
        self.assertGreater(len(targets), 25)
        for attrs in targets:
            self.assertNotIn('hidden', attrs)
            self.assertNotIn('aria-hidden', attrs)
            self.assertNotIn('style', attrs, 'Do not ship hidden initial reveal styles')
        for _, attrs in page.elements:
            if {
                'lore-card',
                'resource-group',
                'utility-card',
                'feature-card',
                'quick-step',
                'tool-card',
            } & set(attrs.get('class', '').split()):
                self.assertIn('data-reveal', attrs)
        scripts = [attrs for tag, attrs in page.elements if tag == 'script']
        animation = next(
            attrs
            for attrs in scripts
            if attrs.get('src') == static('website/js/dist/animations.js')
        )
        self.assertIn('defer', animation)

    def test_no_placeholder_unsupported_claims_or_external_runtime_loaders(self):
        response, _ = self.page()
        html = response.content.decode().lower()
        for forbidden in (
            'terminal:query-protocol',
            'django + tailwind',
            'patron_deity',
            'quests_count',
            'graphql',
            'material-symbols',
            'material-icons',
            'fonts.googleapis',
            'fonts.gstatic',
            'cdn.jsdelivr',
            'unpkg.com',
            'cdn.tailwindcss',
            'bottom-nav',
            'bottom-navigation',
            '99.9%',
            'unlimited requests',
            'no api key required',
            'real-time updates',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, html)
        for path in ('website/js/theme.js', 'website/js/site.js', 'website/js/dist/animations.js'):
            found = finders.find(path)
            self.assertIsNotNone(found, path)
            if found:
                self.assertNotRegex(
                    Path(found).read_text(),
                    r'\bfetch\s*\(|XMLHttpRequest|WebSocket|https?://|import\s*\(',
                )

    def test_response_excerpt_matches_serializer_names_and_seed_without_serializing_models(self):
        response, page = self.page()
        example = json.loads(page.code['response-code'])
        self.assertTrue(example)
        self.assertLessEqual(set(example), set(CharacterDetailSerializer.Meta.fields))
        seed = json.loads((settings.BASE_DIR / 'data/characters.json').read_text())
        percy = next(item for item in seed if item['expected_slug'] == 'percy-jackson')
        expected = {**percy, 'slug': percy['expected_slug'], 'type': 'character'}
        for name, value in example.items():
            with self.subTest(field=name):
                self.assertIn(name, expected)
                self.assertEqual(value, expected[name])
                self.assertIs(type(value), type(expected[name]))
        self.assertEqual(example['slug'], 'percy-jackson')
        self.assertNotIn('patron_deity', example)
        self.assertNotIn('quests_count', example)
        self.assertContains(
            response, 'Illustrative content, not a live request or complete response.'
        )


class HomeContextTests(SimpleTestCase):
    def test_context_uses_request_origin_and_reversed_routes_including_script_prefix(self):
        original_prefix = get_script_prefix()
        try:
            for prefix in ('/', '/archive/'):
                with self.subTest(prefix=prefix), override_settings(ALLOWED_HOSTS=['landing.test']):
                    set_script_prefix(prefix)
                    request = RequestFactory().get(
                        prefix, secure=True, HTTP_HOST='landing.test:8443'
                    )
                    context = get_home_context(request)
                    self.assertEqual(context['origin'], 'https://landing.test:8443')
                    for key, name in (
                        ('api_base_url', 'api-directory'),
                        ('character_url', 'character-detail'),
                    ):
                        kwargs = {'slug': 'percy-jackson'} if name == 'character-detail' else None
                        self.assertEqual(
                            context[key], urljoin(context['origin'], reverse(name, kwargs=kwargs))
                        )
                    self.assertEqual(context['search_url'], f'{reverse("search")}?q=percy')
                    self.assertEqual(
                        context['images_url'], f'{reverse("image-list")}?source_type=wiki'
                    )
                    self.assertEqual(context['search_endpoint'], f'GET {context["search_url"]}')
                    self.assertEqual(context['images_endpoint'], f'GET {context["images_url"]}')
                    self.assertIn(reverse('request-api-key'), context['request_key_raw'])
                    self.assertIn(context['character_url'], context['curl_raw'])
                    self.assertIn('X-API-Key: YOUR_API_KEY', context['request_raw'])
                    for group in context['resource_groups']:
                        for resource in group['resources']:
                            self.assertEqual(resource['url'], reverse(resource['route_name']))
                            self.assertEqual(
                                urlsplit(resource['example_url']).path, resource['url']
                            )
        finally:
            set_script_prefix(original_prefix)

    @override_settings(ALLOWED_HOSTS=['*'])
    def test_untrusted_host_is_escaped_in_code_and_urls(self):
        # Django validates Host even with ALLOWED_HOSTS=['*']; override get_host to
        # exercise the template trust boundary rather than DisallowedHost handling.
        host = 'evil.test"><script>alert("host")</script>&\''
        request = RequestFactory().get('/')
        with patch.object(request, 'get_host', return_value=host):
            context = get_home_context(request)
            response = home(request)
        html = response.content.decode()
        page = LandingHTML(html)
        self.assertNotIn('<script>alert(', html)
        self.assertIn('&lt;script&gt;', html)
        scripts = [attrs for tag, attrs in page.elements if tag == 'script']
        self.assertEqual(len(scripts), 3)
        self.assertTrue(
            all(attrs.get('src', '').startswith(settings.STATIC_URL) for attrs in scripts)
        )
        self.assertIn(host, page.code['request-code'])
        for key, code_id in (('curl_raw', 'curl-code'), ('request_key_raw', 'key-request-code')):
            self.assertEqual(page.code[code_id].strip(), context[key].strip())
        for _, attrs in page.elements:
            self.assertFalse(any(name.startswith('on') for name in attrs))

    def test_component_dynamic_text_and_href_are_escaped(self):
        value = '"><script>alert("component")</script>&'
        template = engines['django'].from_string(
            '{% cotton ui.action :href="value" %}{{ value }}{% endcotton %}'
            '{% cotton ui.code-block id="sample" %}{{ value }}{% endcotton %}'
        )
        html = template.render({'value': value})
        page = LandingHTML(html)
        self.assertEqual(page.links, [value])
        self.assertEqual(page.code['sample'], value)
        self.assertFalse(any(tag == 'script' for tag, _ in page.elements))
        self.assertIn('&lt;script&gt;', html)


class LucideIconTests(SimpleTestCase):
    def render_icon(self, name, attributes='', context=None):
        # In-memory templates bypass Cotton's file loader, so use its equivalent DTL tag.
        template = engines['django'].from_string(
            '{% cotton icons.' + name + ' ' + attributes + ' /%}'
        )
        return ElementTree.fromstring(template.render(context or {}))

    def test_all_vendored_icons_render_as_decorative_inline_svg_by_default(self):
        icon_directory = Path(__file__).parent / 'templates/cotton/icons'
        names = {
            path.stem.replace('_', '-')
            for path in icon_directory.glob('*.html')
            if path.stem != 'base'
        }
        self.assertTrue(
            {
                'arrow-right',
                'book-open',
                'code',
                'copy',
                'external-link',
                'menu',
                'moon',
                'search',
                'sun',
                'x',
            }
            <= names
        )
        for name in sorted(names):
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
