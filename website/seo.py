"""Database-independent metadata and discovery for the public editorial pages."""

import json
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe

SITE_NAME = 'Riordanverse API'
HOME_TITLE = 'Riordanverse API | Percy Jackson REST API for Developers'
HOME_DESCRIPTION = (
    'Build with Riordanverse API: read-only JSON data for Percy Jackson characters, '
    'gods, books, quests and locations. Explore the API docs and request an API key.'
)
GUIDE_TITLE = 'Getting Started with Riordanverse API | Authentication & Examples'
GUIDE_DESCRIPTION = (
    'Learn how to request a Riordanverse API key, fetch Percy Jackson data, filter '
    'results and use pagination with practical REST API examples.'
)
EDITORIAL_ROUTES = ('website:home', 'website:getting-started')
INDEXABLE_ROUTES = (*EDITORIAL_ROUTES, 'swagger-ui', 'redoc')
SITEMAP_ROUTES = (*EDITORIAL_ROUTES, 'swagger-ui')
DISCOVERY_ROUTES = ('website:robots', 'website:sitemap')


def public_url(request, path):
    """Pin production canonicals without hard-coding local or mounted routes."""
    if urlsplit(path).netloc:
        return request.build_absolute_uri(path)
    origin = settings.SEO_PUBLIC_ORIGIN.rstrip('/')
    if origin:
        parts = urlsplit(origin)
        if (
            parts.scheme not in ('http', 'https')
            or not parts.netloc
            or parts.username
            or parts.password
            or parts.path
            or parts.query
            or parts.fragment
        ):
            raise ImproperlyConfigured(
                'SEO_PUBLIC_ORIGIN must be an HTTP(S) origin without a path.'
            )
        return origin + path if path.startswith('/') else request.build_absolute_uri(path)
    return request.build_absolute_uri(path)


def metadata(request, *, guide=False):
    route = 'website:getting-started' if guide else 'website:home'
    return {
        'title': SITE_NAME,
        'page_title': GUIDE_TITLE if guide else HOME_TITLE,
        'description': GUIDE_DESCRIPTION if guide else HOME_DESCRIPTION,
        'url': public_url(request, reverse(route)),
        'image_url': public_url(request, static('website/images/social-preview.png')),
        'image_alt': (
            'Riordanverse API — Riordanverse reference data. '
            'Read-only REST API. Unofficial fan project.'
        ),
    }


def structured_data(request, social, github_url, *, guide=False):
    """Describe the actual project, never fabricated ratings, authors or affiliations."""
    home_url = public_url(request, reverse('website:home'))
    guide_url = public_url(request, reverse('website:getting-started'))
    website_id = home_url + '#website'
    api_id = home_url + '#api'
    graph = [
        {
            '@type': 'WebSite',
            '@id': website_id,
            'name': SITE_NAME,
            'url': home_url,
            'description': HOME_DESCRIPTION,
            'inLanguage': 'en',
            'sameAs': [github_url],
        },
        {
            '@type': 'WebAPI',
            '@id': api_id,
            'name': SITE_NAME,
            'url': public_url(request, reverse('api-directory')),
            'description': (
                'An unofficial, read-only REST API for Riordanverse reference data. '
                'Current coverage focuses on Percy Jackson and related Greek and Roman stories.'
            ),
            'documentation': guide_url,
        },
        {
            '@type': 'WebPage',
            '@id': social['url'] + '#webpage',
            'name': social['page_title'],
            'url': social['url'],
            'description': social['description'],
            'isPartOf': {'@id': website_id},
            'about': {'@id': api_id},
            'inLanguage': 'en',
        },
    ]
    if guide:
        graph[-1]['breadcrumb'] = {'@id': guide_url + '#breadcrumb'}
        graph.append(
            {
                '@type': 'BreadcrumbList',
                '@id': guide_url + '#breadcrumb',
                'itemListElement': [
                    {'@type': 'ListItem', 'position': 1, 'name': SITE_NAME, 'item': home_url},
                    {
                        '@type': 'ListItem',
                        'position': 2,
                        'name': 'Getting started',
                        'item': guide_url,
                    },
                ],
            }
        )
    # JSON inside HTML script data must not allow a closing </script> or HTML injection.
    encoded = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=True)
    return mark_safe(
        encoded.translate(str.maketrans({'<': r'\u003C', '>': r'\u003E', '&': r'\u0026'}))
    )


class SearchIndexingMiddleware:
    """Keep staging and utility/auth/API responses out of search, not behind new auth."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        match = request.resolver_match
        route = match.view_name if match else None
        # Discovery files should be readable without contradictory noindex headers.
        if response.status_code == 200 and route in DISCOVERY_ROUTES:
            return response
        if (
            not settings.SEO_INDEXING_ENABLED
            or route not in INDEXABLE_ROUTES
            or response.status_code != 200
        ):
            response['X-Robots-Tag'] = 'noindex, nofollow'
        return response
