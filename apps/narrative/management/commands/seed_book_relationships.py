"""Seed typed Book relationships from ``data/book_character_relationships.json``.

Seed Books, Characters, Gods, Titans, Monsters, and Creatures first. Missing
entity references warn and are skipped. Character-only compatibility fields are
maintained alongside typed narrator, main-character, and antagonist links.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.bestiary.models import Creature, Monster
from apps.characters.models import Character
from apps.divinities.models import God, Titan
from apps.narrative.models import Book, BookAntagonist, BookMainCharacter, BookNarrator

DATA_FILE = settings.BASE_DIR / 'data' / 'book_character_relationships.json'

ENTITY_MODELS = {
    'character': Character,
    'god': God,
    'titan': Titan,
    'monster': Monster,
    'creature': Creature,
}
ROLE_MODELS = {
    'narrators': BookNarrator,
    'main_characters': BookMainCharacter,
    'antagonists': BookAntagonist,
}
ROLE_LABELS = {
    'narrators': 'narrator',
    'main_characters': 'main character',
    'antagonists': 'antagonist',
}
ENTITY_FIELDS = tuple(ENTITY_MODELS)


def _resolve(model, slug, relation, book_slug, stdout, style):
    if not slug:
        stdout.write(
            style.WARNING(f'[WARN] Missing {relation} slug for book {book_slug} — skipping.')
        )
        return None
    try:
        return model.objects.get(slug=slug)
    except model.DoesNotExist:
        stdout.write(
            style.WARNING(f"[WARN] Unresolved {relation} '{slug}' for book {book_slug} — skipping.")
        )
        return None


def _entity_for_link(link):
    for entity_type in ENTITY_FIELDS:
        entity = getattr(link, entity_type)
        if entity is not None:
            return entity_type, entity
    return None, None


def _narrator_references(entry, book_slug):
    if 'narrators' in entry:
        references = entry['narrators']
        if not isinstance(references, list):
            raise CommandError(f'narrators for Book {book_slug!r} must be a JSON list.')
        if 'narrator_slugs' in entry:
            slugs = entry['narrator_slugs']
            if not isinstance(slugs, list):
                raise CommandError(f'narrator_slugs for Book {book_slug!r} must be a JSON list.')
            character_slugs = [
                reference.get('slug')
                for reference in references
                if isinstance(reference, dict) and reference.get('type') == 'character'
            ]
            if character_slugs != slugs:
                raise CommandError(
                    f'narrator_slugs for Book {book_slug!r} must match its Character narrators.'
                )
        return references

    if 'narrator_slugs' in entry:
        slugs = entry['narrator_slugs']
        if not isinstance(slugs, list):
            raise CommandError(f'narrator_slugs for Book {book_slug!r} must be a JSON list.')
        return [{'type': 'character', 'slug': slug} for slug in slugs]

    if 'narrator_slug' in entry:
        slug = entry['narrator_slug']
        return [{'type': 'character', 'slug': slug}] if slug else []

    return None


class Command(BaseCommand):
    help = 'Seed typed Book narrator, main-character, and antagonist links.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        if not DATA_FILE.exists():
            raise CommandError(f'Book relationship data file not found: {DATA_FILE}')

        with DATA_FILE.open(encoding='utf-8') as data_file:
            entries = json.load(data_file)

        if not isinstance(entries, list):
            raise CommandError('Book relationship data must be a JSON list.')

        book_slugs = [entry.get('book_slug') for entry in entries]
        if any(not slug for slug in book_slugs):
            raise CommandError('Every Book relationship record must have a book_slug.')
        if len(book_slugs) != len(set(book_slugs)):
            raise CommandError('Book relationship data contains duplicate book_slug values.')

        books_synced = 0
        created_count = 0
        narrator_link_count = 0
        main_link_count = 0
        antagonist_link_count = 0

        for entry in entries:
            book_slug = entry['book_slug']
            try:
                book = Book.objects.get(slug=book_slug)
            except Book.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"[WARN] Unresolved Book '{book_slug}' — skipping relationship record."
                    )
                )
                continue

            narrator_references = _narrator_references(entry, book_slug)
            role_references = {}
            if narrator_references is not None:
                role_references['narrators'] = narrator_references
            for relation_name in ('main_characters', 'antagonists'):
                references = entry.get(relation_name, [])
                if not isinstance(references, list):
                    raise CommandError(
                        f'{relation_name} for Book {book_slug!r} must be a JSON list.'
                    )
                role_references[relation_name] = references

            books_synced += 1
            for relation_name, link_model in ROLE_MODELS.items():
                if relation_name not in role_references:
                    continue
                references = role_references[relation_name]
                desired = {}
                for reference in references:
                    if not isinstance(reference, dict):
                        self.stdout.write(
                            self.style.WARNING(
                                f'[WARN] Invalid {relation_name} reference for '
                                f'{book_slug} — skipping.'
                            )
                        )
                        continue

                    entity_type = reference.get('type')
                    model = ENTITY_MODELS.get(entity_type)
                    if model is None:
                        self.stdout.write(
                            self.style.WARNING(
                                f"[WARN] Unknown entity type '{entity_type}' in "
                                f'{relation_name} for {book_slug} — skipping.'
                            )
                        )
                        continue

                    slug = reference.get('slug')
                    entity = _resolve(
                        model,
                        slug,
                        f'{entity_type} {ROLE_LABELS[relation_name]}',
                        book_slug,
                        self.stdout,
                        self.style,
                    )
                    if entity is not None:
                        key = (entity_type, entity.pk)
                        if key in desired:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'[WARN] Duplicate {entity_type} '
                                    f'{ROLE_LABELS[relation_name]} '
                                    f"'{slug}' for {book_slug} — skipping duplicate."
                                )
                            )
                            continue
                        desired[key] = entity

                current_links = list(
                    link_model.objects.filter(book=book).select_related(*ENTITY_FIELDS)
                )
                for link in current_links:
                    current_type, current_entity = _entity_for_link(link)
                    if current_type is None or (current_type, current_entity.pk) not in desired:
                        link.delete()

                for (entity_type, _), entity in desired.items():
                    _, created = link_model.objects.get_or_create(
                        book=book,
                        **{entity_type: entity},
                    )
                    created_count += int(created)
                    if relation_name == 'narrators':
                        narrator_link_count += 1
                    elif relation_name == 'main_characters':
                        main_link_count += 1
                    else:
                        antagonist_link_count += 1

                if relation_name == 'narrators':
                    legacy_narrator = None
                    if len(desired) == 1:
                        (entity_type, _), entity = next(iter(desired.items()))
                        if entity_type == 'character':
                            legacy_narrator = entity
                    if book.narrator_id != (legacy_narrator.pk if legacy_narrator else None):
                        book.narrator = legacy_narrator
                        book.save(update_fields=['narrator'])

        self.stdout.write(
            self.style.SUCCESS(
                f'Book relationships seeded: {books_synced} books synchronized, '
                f'{created_count} links created; '
                f'{narrator_link_count} narrator links, '
                f'{main_link_count} main-character links, and '
                f'{antagonist_link_count} antagonist links resolved.'
            )
        )
