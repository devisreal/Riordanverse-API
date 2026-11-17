from xml.etree.ElementTree import Element, SubElement, tostring

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_safe

from website.content import GITHUB_URL, get_home_context
from website.seo import EDITORIAL_ROUTES, metadata, public_url, structured_data


def home(request):
    return render(request, 'website/home.html', get_home_context(request))


def getting_started(request):
    context = get_home_context(request)
    social = metadata(request, guide=True)
    context.update(
        social=social,
        structured_data=structured_data(request, social, GITHUB_URL, guide=True),
        guide_request_key_raw=context['request_key_raw'],
        guide_request_raw=(
            f'curl "{request.build_absolute_uri(reverse("character-list"))}'
            '?divine_parent=poseidon&is_demigod=true&sort=name&order=asc&page=1&limit=20" \\\n'
            '  -H "X-API-Key: $API_KEY"'
        ),
    )
    return render(request, 'website/getting_started.html', context)


@require_safe
def robots(request):
    if settings.SEO_INDEXING_ENABLED:
        content = (
            'User-agent: *\nAllow: /\n\n'
            f'Sitemap: {public_url(request, reverse("website:sitemap"))}\n'
        )
    else:
        # Crawlers must be able to fetch pages to observe their noindex headers.
        content = 'User-agent: *\nAllow: /\n'
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Cache-Control'] = 'public, max-age=300'
    return response


@require_safe
def sitemap(request):
    root = Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    if settings.SEO_INDEXING_ENABLED:
        for route in EDITORIAL_ROUTES:
            entry = SubElement(root, 'url')
            SubElement(entry, 'loc').text = public_url(request, reverse(route))
    response = HttpResponse(
        tostring(root, encoding='utf-8', xml_declaration=True),
        content_type='application/xml; charset=utf-8',
    )
    response['Cache-Control'] = 'public, max-age=300'
    return response
