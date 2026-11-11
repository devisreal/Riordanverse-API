"""Static landing-page copy and illustrative examples; never query the API or database.

Route names are resolved per request. Snippet HTML is trusted only after Pygments
has escaped it; URLs, copy, and raw snippets remain ordinary template strings.
"""

import json
from shlex import quote
from urllib.parse import urlencode

from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import BashLexer, HttpLexer, JsonLexer, TextLexer

GITHUB_URL = 'https://github.com/devisreal/Percy-Jackson-Fandom-API'


def _resource(label, route_name, description, **filters):
    return {
        'label': label,
        'route_name': route_name,
        'description': description,
        'query': urlencode(filters),
    }


RESOURCE_GROUPS = (
    {
        'title': 'People & Divinities',
        'icon': 'person_pin',
        'description': 'Characters, major and minor gods, titans, and familial lines.',
        'resources': (
            _resource(
                'Characters',
                'character-list',
                'Demigods, mortals, and their stories.',
                is_demigod='true',
                sort='name',
                order='asc',
            ),
            _resource(
                'Gods',
                'god-list',
                'Divine domains, cabins, and family connections.',
                tier='olympian',
                sort='name',
                order='asc',
            ),
            _resource(
                'Titans',
                'titan-list',
                'Titan generations, alignments, and histories.',
                generation='elder_titan',
                sort='name',
                order='asc',
            ),
        ),
    },
    {
        'title': 'Stories & Narrative',
        'icon': 'auto_stories',
        'description': 'Book timelines, mythological prophecies, historic quests, and pivotal events.',
        'resources': (
            _resource(
                'Books',
                'book-list',
                'Publication details and connected lore.',
                book_type='novel',
                sort='book_number',
                order='asc',
            ),
            _resource(
                'Quests',
                'quest-list',
                'Quest leaders, participants, and outcomes.',
                led_by='percy-jackson',
                sort='title',
                order='asc',
            ),
            _resource(
                'Prophecies',
                'prophecy-list',
                'Prophetic verses and their subjects.',
                subject='percy-jackson',
                sort='title',
                order='asc',
            ),
            _resource(
                'Events',
                'event-list',
                'Battles and turning points across the books.',
                book='the-lightning-thief',
            ),
        ),
    },
    {
        'title': 'Places & Factions',
        'icon': 'apartment',
        'description': 'Geographic landmarks, mortal/immortal camps, deity cabins, and factions.',
        'resources': (
            _resource(
                'Locations',
                'location-list',
                'Camps, divine realms, and mortal landmarks.',
                location_type='camp',
                sort='name',
                order='asc',
            ),
            _resource(
                'Cabins',
                'cabin-list',
                'Camp Half-Blood cabins and their deities.',
                is_honorary='false',
                sort='number',
                order='asc',
            ),
            _resource(
                'Factions',
                'faction-list',
                'Camps, armies, councils, and other allegiances.',
                faction_type='camp',
                sort='name',
                order='asc',
            ),
        ),
    },
    {
        'title': 'Bestiary & Regalia',
        'icon': 'swords',
        'description': 'Mythological monsters, creatures, weapons, and magical artifacts.',
        'resources': (
            _resource(
                'Monsters',
                'monster-list',
                'Mythological adversaries and their defeats.',
                can_reform='true',
                sort='name',
                order='asc',
            ),
            _resource(
                'Creatures',
                'creature-list',
                'Mythical beings and their allegiances.',
                sort='name',
                order='asc',
            ),
            _resource(
                'Weapons & Relics',
                'weapon-list',
                'Materials, transformations, and wielders.',
                material='celestial_bronze',
                sort='name',
                order='asc',
            ),
        ),
    },
)

FEATURES = (
    {
        'title': 'Connected lore',
        'icon': 'hub',
        'description': 'Follow family relationships, related-entity slugs, and nested REST '
        'collections connecting characters, divinities, books, and quests.',
    },
    {
        'title': 'Filtering and sorting',
        'icon': 'filter_list',
        'description': 'Use resource-specific filters and supported sort fields with '
        'sort and order=asc or order=desc. Available fields vary by collection.',
    },
    {
        'title': 'Paginated collections',
        'icon': 'dataset',
        'description': 'Collection envelopes contain data and meta with total, page, limit, '
        'and total_pages. Use page and limit; the default is 20, with a maximum of 100.',
    },
    {
        'title': 'Character powers',
        'icon': 'bolt',
        'description': 'Character details embed powers with sources, types, and limitations. '
        'Dedicated character power endpoints support filtering and sorting.',
    },
    {
        'title': 'Images and provenance',
        'icon': 'history_edu',
        'description': 'Explore image references, source and attribution metadata, '
        'entity galleries, and Riordan Wiki links.',
    },
    {
        'title': 'Documented access',
        'icon': 'menu_book',
        'description': 'Explore Swagger UI, ReDoc, and the OpenAPI schema. Request an API key '
        'and send it in the X-API-Key header for protected endpoints.',
    },
)

TOOLS = (
    {
        'title': 'Interactive API Docs',
        'icon': 'terminal',
        'route_name': 'swagger-ui',
        'description': 'Explore endpoints and try authenticated requests in Swagger UI.',
    },
    {
        'title': 'API Reference (ReDoc)',
        'icon': 'description',
        'route_name': 'redoc',
        'description': 'Read the generated API reference and response schemas.',
    },
    {
        'title': 'OpenAPI Schema',
        'icon': 'data_object',
        'route_name': 'schema',
        'description': 'Use the machine-readable schema with your development tools.',
    },
    {
        'title': 'Contribute on GitHub',
        'icon': 'code',
        'url': GITHUB_URL,
        'external': True,
        'description': 'Browse the source, report issues, and contribute to the project.',
    },
)

LORE_CARDS = (
    {
        'title': 'Camp Half-Blood Sound',
        'eyebrow': 'Sanctuary Core',
        'description': 'Explore Camp Half-Blood, its cabins, and the places that shelter demigods.',
        'image': 'website/images/lore-camp.webp',
        'image_alt': 'Illustrated aerial view of Camp Half-Blood, its cabins, lake, and Big House.',
        'image_width': 1000,
        'image_height': 622,
        'image_credit_prefix': 'Image:',
        'image_credit': 'Riordan Wiki',
        'image_source_url': 'https://riordan.fandom.com/wiki/File:Camp_Half-Blood_IE.jpg',
        'route_name': 'location-list',
    },
    {
        'title': 'Olympian Pantheons',
        'eyebrow': 'Schema Graph',
        'description': 'Discover gods, titans, and the family relationships connecting their stories.',
        'image': 'website/images/lore-olympus.webp',
        'image_alt': 'Ceiling fresco with classical mythological figures gathered among clouds.',
        'image_width': 1000,
        'image_height': 667,
        'image_credit_prefix': 'Image:',
        'image_credit': 'Visit Olympus',
        'image_source_url': (
            'https://visitolympus.travel/a-guide-to-the-gods-and-legends-of-mount-olympus/'
        ),
        'route_name': 'god-list',
    },
    {
        'title': 'Weapons & Regalia',
        'eyebrow': 'Artifact Index',
        'description': 'Celestial bronze and Stygian iron, transformational abilities, and wielders.',
        'image': 'website/images/lore-trident.webp',
        'image_alt': 'Close-up of a bronze Neptune trident against a blue, cloud-filled sky.',
        'image_width': 1000,
        'image_height': 562,
        'image_credit_prefix': 'Cropped photo:',
        'image_credit': 'Oceancetaceen / Commons',
        'image_source_url': (
            'https://commons.wikimedia.org/wiki/'
            'File:Neptunbrunnen_Detail_Dreizack_(Alice_Chodura).JPG'
        ),
        'image_license': 'CC BY-SA 3.0',
        'image_license_url': 'https://creativecommons.org/licenses/by-sa/3.0/',
        'route_name': 'weapon-list',
    },
)

NAVIGATION = (
    {'label': 'Resources', 'url': '#resources'},
    {'label': 'Features', 'url': '#features'},
    {'label': 'Quick Start', 'url': '#quick-start'},
    {'label': 'Documentation', 'route_name': 'swagger-ui'},
    {'label': 'GitHub', 'url': GITHUB_URL},
)

# A subset of CharacterDetailSerializer fields, using data/characters.json.
# Omit database-generated IDs, timestamps, and relationship-dependent fields.
RESPONSE_JSON = json.dumps(
    {
        'slug': 'percy-jackson',
        'name': 'Percy Jackson',
        'character_type': 'demigod',
        'species': 'demigod',
        'gender': 'male',
        'status': 'alive',
        'greek_or_roman': 'greek',
        'age_first_appearance': 12,
        'type': 'character',
        'cabin_number': 3,
        'fatal_flaw': 'Personal loyalty',
        'is_demigod': True,
        'is_big_three_child': True,
        'wiki_url': 'https://riordan.fandom.com/wiki/Percy_Jackson',
    },
    indent=2,
)
EXAMPLE_NOTICE = 'Illustrative content, not a live request or complete response.'


def _linked(item):
    """Return a fresh dictionary so request handling never mutates static copy."""
    result = dict(item)
    if 'route_name' in result:
        result['url'] = reverse(result['route_name'])
    return result


def _lore_card(item):
    card = _linked(item)
    stem = item['image'].removesuffix('.webp')
    card['image_sources'] = [
        {'path': f'{stem}-{width}.webp', 'width': width} for width in (256, 384, 512, 768)
    ] + [{'path': item['image'], 'width': item['image_width']}]
    return card


def _code(source, lexer):
    return mark_safe(highlight(source, lexer, HtmlFormatter(nowrap=True, classprefix='syntax-')))


def get_home_context(request):
    """Build landing context without network calls, model imports, or database access.

    Each code sample has a plain *_raw value for copy controls and a highlighted
    *_code value for rendering inside <pre><code>. Do not apply safe to raw values.
    """
    origin = request.build_absolute_uri('/').rstrip('/')
    character_url = request.build_absolute_uri(
        reverse('character-detail', kwargs={'slug': 'percy-jackson'})
    )
    key_url = request.build_absolute_uri(reverse('request-api-key'))
    payload = json.dumps({'consumer_name': 'Camp Half-Blood App', 'email': 'you@example.com'})
    request_key_raw = (
        f'curl -X POST {quote(key_url)} \\\n'
        '  -H "Content-Type: application/json" \\\n'
        f'  --data {quote(payload)}'
    )
    header_raw = 'X-API-Key: YOUR_API_KEY'
    curl_raw = f'curl {quote(character_url)} \\\n  -H "X-API-Key: YOUR_API_KEY"'  # gitleaks:allow -- public placeholder, not a credential
    request_raw = (
        f'GET {reverse("character-detail", kwargs={"slug": "percy-jackson"})} HTTP/1.1\n'
        f'Host: {request.get_host()}\nAccept: application/json\n{header_raw}'
    )
    groups = []
    for group in RESOURCE_GROUPS:
        resources = []
        for item in group['resources']:
            resource = _linked(item)
            resource['example_url'] = f'{resource["url"]}?{resource["query"]}'
            resources.append(resource)
        groups.append(
            {**group, 'resources': resources, 'example_query': resources[0]['query'].split('&')[0]}
        )

    search_url = f'{reverse("search")}?{urlencode({"q": "percy"})}'
    images_url = f'{reverse("image-list")}?{urlencode({"source_type": "wiki"})}'
    return {
        'origin': origin,
        'social': {
            'title': 'Percy Jackson Fandom API',
            'description': (
                'A structured, read-only REST API for Riordanverse characters, gods, quests, '
                'locations, and the relationships connecting them.'
            ),
            # Canonical links omit tracking/query parameters and respect mounted deployments.
            'url': request.build_absolute_uri(reverse('website:home')),
            'image_url': request.build_absolute_uri(static('website/images/social-preview.png')),
            'image_alt': (
                'Percy Jackson Fandom API — Riordanverse reference data. '
                'Read-only REST API. Unofficial fan project.'
            ),
        },
        'api_base_url': request.build_absolute_uri(reverse('api-directory')),
        'api_directory_url': reverse('api-directory'),
        'docs_url': reverse('swagger-ui'),
        'search_url': search_url,
        'images_url': images_url,
        'search_endpoint': f'GET {search_url}',
        'images_endpoint': f'GET {images_url}',
        'request_key_url': reverse('request-api-key'),
        'github_url': GITHUB_URL,
        'resource_groups': groups,
        'features': FEATURES,
        'tools': [_linked(item) for item in TOOLS],
        'lore_cards': [_lore_card(item) for item in LORE_CARDS],
        'navigation': [_linked(item) for item in NAVIGATION],
        'example_notice': EXAMPLE_NOTICE,
        'character_url': character_url,
        'request_raw': request_raw,
        'request_code': _code(request_raw, HttpLexer()),
        'response_json': RESPONSE_JSON,
        'response_code': _code(RESPONSE_JSON, JsonLexer()),
        'request_key_raw': request_key_raw,
        'request_key_code': _code(request_key_raw, BashLexer()),
        'header_raw': header_raw,
        'header_code': _code(header_raw, TextLexer()),
        'curl_raw': curl_raw,
        'curl_code': _code(curl_raw, BashLexer()),
    }
