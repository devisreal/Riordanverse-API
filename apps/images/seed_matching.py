"""URL-filename matching rules for entity-specific wiki image galleries."""

import re
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

ENTITY_URL_MATCH_TYPES = frozenset({'characters', 'gods', 'titans', 'monsters', 'weapons'})
_TITLE_PREFIXES_TO_DROP = (
    ('percy', 'jackson', 'and', 'the'),
    ('percy', 'jacksons'),
)
_STOP_WORDS = frozenset({'a', 'an', 'and', 'of', 'the'})


def _tokens(value):
    value = value.casefold().replace("'s", 's').replace('’s', 's')
    return re.findall(r'[a-z0-9]+', value)


def _filename_tokens(image_url):
    if not image_url:
        return ()

    path = unquote(urlsplit(image_url).path).split('/revision/', maxsplit=1)[0]
    filename = PurePosixPath(path).name
    stem = filename.rsplit('.', maxsplit=1)[0]
    return tuple(_tokens(stem))


def _contains_sequence(haystack, needle):
    if not needle or len(needle) > len(haystack):
        return False
    return any(
        haystack[index : index + len(needle)] == needle
        for index in range(len(haystack) - len(needle) + 1)
    )


def _aliases(name, slug):
    aliases = []
    for value in (name, slug):
        tokens = tuple(_tokens(value or ''))
        if tokens and tokens not in aliases:
            aliases.append(tokens)
        if tokens and tokens[0] in {'a', 'an', 'the'} and tokens[1:] not in aliases:
            aliases.append(tokens[1:])
    return aliases


def _filename_matches_alias(filename_tokens, alias):
    if _contains_sequence(filename_tokens, alias):
        return True
    compact_alias = ''.join(alias)
    compact_filename = ''.join(filename_tokens)
    return len(compact_alias) >= 5 and compact_alias in compact_filename


def image_url_matches_entity(image_url, *, entity_name, entity_slug):
    """Match an entity against the image URL filename, never its source page URL."""
    filename_tokens = _filename_tokens(image_url)
    return any(
        _filename_matches_alias(filename_tokens, alias)
        for alias in _aliases(entity_name, entity_slug)
    )


def _book_title_aliases(title, slug):
    aliases = _aliases(title, slug)
    title_tokens = _tokens(title or '')
    for prefix in _TITLE_PREFIXES_TO_DROP:
        if title_tokens[: len(prefix)] == prefix:
            core_title = title_tokens[len(prefix) :]
            if core_title and core_title not in aliases:
                aliases.append(core_title)
            break
    return [
        tuple(token for token in alias if token not in _STOP_WORDS)
        for alias in aliases
        if any(token not in _STOP_WORDS for token in alias)
    ]


def is_book_cover(image, *, book_title, book_slug):
    """Keep explicit cover files and portrait files named for the book."""
    filename_tokens = _filename_tokens(image.get('url'))
    if not filename_tokens or {'movie', 'concept'} & set(filename_tokens):
        return False

    if any(
        token == 'cvr' or token.startswith(('cover', 'bookpic')) or token.endswith('cover')
        for token in filename_tokens
    ):
        return True

    width = image.get('width') or 0
    height = image.get('height') or 0
    if height <= width:
        return False

    compact_filename = ''.join(filename_tokens)
    for alias in _book_title_aliases(book_title, book_slug):
        if _contains_sequence(filename_tokens, alias):
            return True
        compact_alias = ''.join(alias)
        if len(compact_alias) >= 7 and compact_alias in compact_filename:
            return True
    return False


def should_link_image(entity_type, entity_name, entity_slug, image):
    """Apply conservative URL-name matching to entity galleries."""
    if entity_type == 'books':
        return is_book_cover(image, book_title=entity_name, book_slug=entity_slug)
    if entity_type in ENTITY_URL_MATCH_TYPES:
        return image_url_matches_entity(
            image.get('url'), entity_name=entity_name, entity_slug=entity_slug
        )
    return True
