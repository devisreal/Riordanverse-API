"""Read-only MediaWiki image auditing for fandom-hosted source pages."""

from __future__ import annotations

import html
import json
import re
import ssl
import time
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

import certifi

MAX_TITLES_PER_QUERY = 50
DEFAULT_USER_AGENT = (
    'RiordanverseImageAudit/1.0 (https://github.com/devisreal/Percy-Jackson-Fandom-API)'
)

_ALLOWED_LICENSE_PATHS = (
    re.compile(r'^/licenses/by/(?:1\.0|2\.0|2\.5|3\.0|4\.0)/?$'),
    re.compile(r'^/licenses/by-sa/(?:1\.0|2\.0|2\.5|3\.0|4\.0)/?$'),
    re.compile(r'^/publicdomain/zero/1\.0/?$'),
)


class WikiImageAuditError(Exception):
    """Raised when a MediaWiki page or API response cannot be audited."""


class _HTMLTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.links = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self.links.append(href)


def _metadata_value(metadata, key):
    item = metadata.get(key)
    if isinstance(item, dict):
        return item.get('value')
    return None


def _clean_metadata_value(value):
    if not value:
        return None
    parser = _HTMLTextParser()
    parser.feed(str(value))
    text = ' '.join(' '.join(parser.parts).split())
    return html.unescape(text) or None


def is_allowlisted_license(license_url):
    """Allow explicit CC BY, CC BY-SA, and CC0 URLs; reject all else."""
    if not license_url:
        return False

    parsed = urlparse(license_url.strip())
    if parsed.scheme != 'https' or parsed.hostname not in {
        'creativecommons.org',
        'www.creativecommons.org',
    }:
        return False

    path = parsed.path.lower()
    return any(pattern.fullmatch(path) for pattern in _ALLOWED_LICENSE_PATHS)


def _api_url_and_title(page_url):
    parsed = urlparse(page_url)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise WikiImageAuditError(f'Invalid wiki page URL: {page_url}')
    if parsed.hostname not in {'riordan.fandom.com', 'www.riordan.fandom.com'}:
        raise WikiImageAuditError(f'Unsupported wiki host: {parsed.hostname}')

    path_parts = parsed.path.split('/wiki/', maxsplit=1)
    if len(path_parts) != 2 or not path_parts[1]:
        raise WikiImageAuditError(f'Wiki URL must contain /wiki/<title>: {page_url}')

    title = unquote(path_parts[1].split('/', maxsplit=1)[0]).replace('_', ' ')
    return f'https://{parsed.netloc}/api.php', title


class FandomImageAuditClient:
    """Fetch page image metadata without downloading or publishing image files."""

    def __init__(self, *, user_agent=DEFAULT_USER_AGENT, timeout=20, request_delay=0.25):
        self.user_agent = user_agent
        self.timeout = timeout
        self.request_delay = request_delay
        self._last_request_at = 0.0

    def _request(self, api_url, params):
        delay = self.request_delay - (time.monotonic() - self._last_request_at)
        if delay > 0:
            time.sleep(delay)

        request_url = f'{api_url}?{urlencode(params)}'
        request = Request(request_url, headers={'User-Agent': self.user_agent})
        self._last_request_at = time.monotonic()
        try:
            tls_context = ssl.create_default_context(cafile=certifi.where())
            with urlopen(request, timeout=self.timeout, context=tls_context) as response:
                payload = json.load(response)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise WikiImageAuditError(f'MediaWiki API request failed: {exc}') from exc

        if api_error := payload.get('error'):
            raise WikiImageAuditError(f'MediaWiki API error: {api_error}')
        return payload

    def _image_titles(self, api_url, page_title):
        params = {
            'action': 'query',
            'format': 'json',
            'formatversion': 2,
            'prop': 'images',
            'titles': page_title,
            'imlimit': 'max',
            'redirects': '1',
        }
        titles = []
        while True:
            payload = self._request(api_url, params)
            pages = payload.get('query', {}).get('pages', [])
            titles.extend(
                image['title']
                for page in pages
                for image in page.get('images', [])
                if image.get('title')
            )
            if not (continuation := payload.get('continue')):
                break
            params.update(continuation)
        return list(dict.fromkeys(titles))

    def _image_info(self, api_url, titles):
        results = {}
        for start in range(0, len(titles), MAX_TITLES_PER_QUERY):
            batch = titles[start : start + MAX_TITLES_PER_QUERY]
            payload = self._request(
                api_url,
                {
                    'action': 'query',
                    'format': 'json',
                    'formatversion': 2,
                    'prop': 'imageinfo',
                    'iiprop': 'url|size|extmetadata',
                    'iiurlwidth': 1200,
                    'titles': '|'.join(batch),
                },
            )
            for page in payload.get('query', {}).get('pages', []):
                results[page.get('title')] = page.get('imageinfo', [{}])[0]
        return results

    def scan_page(self, page_url, *, include_all_images=False):
        api_url, page_title = _api_url_and_title(page_url)
        image_titles = self._image_titles(api_url, page_title)
        image_infos = self._image_info(api_url, image_titles)
        file_page_base = api_url.removesuffix('/api.php') + '/wiki/'

        allowlisted_images = []
        excluded_images = []
        for title in image_titles:
            info = image_infos.get(title)
            if not info:
                excluded_images.append({'file_title': title, 'reason': 'missing image metadata'})
                continue

            metadata = info.get('extmetadata') or {}
            license_name = _clean_metadata_value(_metadata_value(metadata, 'LicenseShortName'))
            license_url = _clean_metadata_value(_metadata_value(metadata, 'LicenseUrl'))
            if not include_all_images and not is_allowlisted_license(license_url):
                excluded_images.append(
                    {
                        'file_title': title,
                        'reason': 'license is missing or not on the reuse allowlist',
                        'license': license_name,
                        'license_url': license_url,
                    }
                )
                continue

            artist = _metadata_value(metadata, 'Artist')
            artist_parser = _HTMLTextParser()
            if artist:
                artist_parser.feed(str(artist))
            object_name = _clean_metadata_value(_metadata_value(metadata, 'ObjectName'))
            file_path = quote(title.replace(' ', '_'), safe=':')
            file_name = title.removeprefix('File:')
            alt_text = object_name or file_name.rsplit('.', 1)[0]
            file_format = (info.get('mime') or '').removeprefix('image/').lower()
            if not file_format and '.' in file_name:
                file_format = file_name.rsplit('.', 1)[-1].lower()
            image = {
                'file_title': title,
                'url': info.get('url'),
                'thumbnail_url': info.get('thumburl'),
                'alt_text': alt_text[:255],
                'source_url': page_url,
                'wiki_url': file_page_base + file_path,
                'license': license_name,
                'license_url': license_url,
                'artist_name': _clean_metadata_value(artist),
                'artist_url': urljoin(file_page_base, artist_parser.links[0])
                if artist_parser.links
                else None,
                'width': info.get('width'),
                'height': info.get('height'),
                'file_format': file_format or None,
                'license_status': 'allowlisted_candidate',
            }
            if include_all_images:
                image['license'] = None
                image['license_url'] = None
                image['license_status'] = 'not_recorded'
                if not image['url']:
                    excluded_images.append(
                        {'file_title': title, 'reason': 'missing direct image URL'}
                    )
                    continue
                allowlisted_images.append(image)
            else:
                allowlisted_images.append(image)

        return {
            'source_page_url': page_url,
            'images': allowlisted_images,
            'excluded_images': excluded_images,
            'use_placeholder': not allowlisted_images,
        }
