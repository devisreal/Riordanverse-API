"""Seed Character records from ``data/characters.json``.

Books, Gods, and Titans should be seeded first. Unresolved foreign-key
references are warned about and set to null; unresolved many-to-many and
slug references are warned about and omitted.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from apps.characters.models import Character
from apps.core.seed_utils import update_or_create_by_expected_slug
from apps.divinities.models import God, Titan
from apps.narrative.models import Book

DATA_FILE = settings.BASE_DIR / 'data' / 'characters.json'

SCALAR_FIELDS = (
    'aliases',
    'character_type',
    'species',
    'gender',
    'status',
    'greek_or_roman',
    'age_first_appearance',
    'mortal_parent_name',
    'cabin_number',
    'affiliation',
    'fatal_flaw',
    'can_see_through_mist',
    'has_adhd',
    'has_dyslexia',
    'is_demigod',
    'is_big_three_child',
    'is_hunter_of_artemis',
    'is_oracle',
    'is_possessed',
    'appearance',
    'personality_traits',
    'special_states',
    'quote',
    'description',
    'lore_notes',
)


def _warning(stdout, style, message):
    stdout.write(style.WARNING(f'[WARN] {message}'))


def _resolve_book(slug, owner, stdout, style):
    if not slug:
        return None
    try:
        return Book.objects.get(slug=slug)
    except Book.DoesNotExist:
        _warning(stdout, style, f"Unresolved book '{slug}' for {owner} — skipping link.")
        return None


def _resolve_divine_parent(slug, owner, stdout, style):
    if not slug:
        return None, None
    try:
        return God.objects.get(slug=slug), None
    except God.DoesNotExist:
        try:
            return None, Titan.objects.get(slug=slug)
        except Titan.DoesNotExist:
            _warning(
                stdout,
                style,
                f"Unresolved divine parent '{slug}' for {owner} — skipping link.",
            )
            return None, None


class Command(BaseCommand):
    help = 'Seed characters from data/characters.json with soft reference resolution.'

    def handle(self, *args, **kwargs):
        if not DATA_FILE.exists():
            self.stdout.write(self.style.ERROR(f'Data file not found: {DATA_FILE}'))
            return

        with DATA_FILE.open(encoding='utf-8') as data_file:
            entries = json.load(data_file)

        created_count = 0
        updated_count = 0
        error_count = 0
        by_expected_slug = {}
        pending = []

        # First pass creates every character so self-references can resolve later.
        for entry in entries:
            name = entry.get('name', 'unknown')
            try:
                defaults = {field: entry[field] for field in SCALAR_FIELDS if field in entry}
                if entry.get('wiki_url'):
                    defaults['wiki_url'] = entry['wiki_url']

                expected_slug = entry.get('expected_slug')
                if expected_slug:
                    defaults['slug'] = expected_slug

                if 'divine_parent_slug' in entry:
                    god_parent, titan_parent = _resolve_divine_parent(
                        entry['divine_parent_slug'], name, self.stdout, self.style
                    )
                    defaults['divine_parent'] = god_parent
                    defaults['divine_parent_titan'] = titan_parent

                first_book_slug = entry.get('first_appearance_book_slug')
                defaults['first_appearance_book'] = _resolve_book(
                    first_book_slug, name, self.stdout, self.style
                )

                if expected_slug:
                    character, created = update_or_create_by_expected_slug(
                        Character,
                        expected_slug,
                        defaults,
                        fallback={'name': name},
                    )
                else:
                    character, created = Character.all_objects.update_or_create(
                        name=name,
                        defaults=defaults,
                    )
                if expected_slug:
                    by_expected_slug[expected_slug] = character
                    if character.slug != expected_slug:
                        _warning(
                            self.stdout,
                            self.style,
                            f"Expected slug '{expected_slug}' for {name}, got "
                            f"'{character.slug}' — references use the resolved record.",
                        )
                pending.append((entry, character))

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created: {name}'))
                else:
                    updated_count += 1
                    self.stdout.write(f'  Updated: {name}')
            except (DatabaseError, KeyError, TypeError, ValueError) as exc:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'  Failed: {name} — {exc}'))

        # Second pass resolves character and book relationships without aborting
        # the command when individual references are missing.
        for entry, character in pending:
            owner = entry.get('name', character.name)
            try:
                update_fields = []
                if 'mortal_parent_ref_slug' in entry:
                    parent_slug = entry.get('mortal_parent_ref_slug')
                    parent = by_expected_slug.get(parent_slug) if parent_slug else None
                    if parent_slug and parent is None:
                        _warning(
                            self.stdout,
                            self.style,
                            f"Unresolved mortal parent '{parent_slug}' for {owner} — skipping link.",
                        )
                    character.mortal_parent_ref = parent
                    update_fields.append('mortal_parent_ref')

                if 'empathy_link_slug' in entry:
                    empathy_slug = entry.get('empathy_link_slug')
                    empathy_link = by_expected_slug.get(empathy_slug) if empathy_slug else None
                    if empathy_slug and empathy_link is None:
                        _warning(
                            self.stdout,
                            self.style,
                            f"Unresolved empathy-link character '{empathy_slug}' for {owner} "
                            '— skipping link.',
                        )
                    character.empathy_link = empathy_link
                    update_fields.append('empathy_link')
                if update_fields:
                    character.save(update_fields=(*update_fields, 'updated_at'))

                if 'sibling_slugs' in entry:
                    siblings = []
                    for slug in entry.get('sibling_slugs', []):
                        sibling = by_expected_slug.get(slug)
                        if sibling is None:
                            _warning(
                                self.stdout,
                                self.style,
                                f"Unresolved sibling '{slug}' for {owner} — omitting reference.",
                            )
                        else:
                            siblings.append(sibling)
                    character.siblings.set(siblings)

                if 'books_appeared_in_slugs' in entry:
                    books = []
                    for slug in entry['books_appeared_in_slugs']:
                        book = _resolve_book(slug, owner, self.stdout, self.style)
                        if book is not None:
                            books.append(book)
                    character.books_appeared_in.set(books)
            except (DatabaseError, KeyError, TypeError, ValueError) as exc:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'  Failed relationships for {owner} — {exc}'))

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Characters seeded: {created_count} created, '
                f'{updated_count} updated, {error_count} errors.'
            )
        )
