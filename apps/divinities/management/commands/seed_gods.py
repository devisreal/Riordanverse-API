"""
Management command: seed_gods
Loads all V1 God records from data/gods.json.

Re-run safe: uses update_or_create on name.

Dependency order:
- Books must be seeded first (seed_books) — references first_appearance_book
  and books_appeared_in by slug.

Deferred until all referenced entities exist:
- children_demigods, weapons, and sibling relationships — populated by seed_divine_relationships
"""

import json

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from apps.divinities.models import God
from apps.narrative.models import Book

DATA_FILE = settings.BASE_DIR / 'data' / 'gods.json'


def _get_book(slug, god_name, stdout, style):
    """Resolve a book slug and emit a warning rather than failing the seed."""
    try:
        return Book.objects.get(slug=slug)
    except Book.DoesNotExist:
        stdout.write(
            style.WARNING(
                f"  Warning: Book '{slug}' not found for {god_name} — skipping that reference."
            )
        )
        return None


class Command(BaseCommand):
    help = 'Seed V1 God records from data/gods.json'

    def handle(self, *args, **kwargs):
        if not DATA_FILE.exists():
            self.stdout.write(self.style.ERROR(f'Data file not found: {DATA_FILE}'))
            return

        with DATA_FILE.open(encoding='utf-8') as data_file:
            gods = json.load(data_file)

        created_count = 0
        updated_count = 0
        error_count = 0

        for entry in gods:
            try:
                defaults = {
                    'roman_name': entry.get('roman_name'),
                    'mythology': entry.get('mythology', 'greek'),
                    'tier': entry.get('tier', 'olympian'),
                    'affiliation': entry.get('affiliation', 'olympian_council'),
                    'status': entry.get('status', 'immortal'),
                    'domains': entry.get('domains', []),
                    'symbols': entry.get('symbols', []),
                    'sacred_animals': entry.get('sacred_animals', []),
                    'sacred_plants': entry.get('sacred_plants', []),
                    'sacred_items': entry.get('sacred_items', []),
                    'cabin_number': entry.get('cabin_number'),
                    'has_cabin': entry.get('has_cabin', False),
                    'is_big_three': entry.get('is_big_three', False),
                    'oath_status': entry.get('oath_status', 'not_applicable'),
                    'greek_aspect_personality': entry.get('greek_aspect_personality'),
                    'roman_aspect_personality': entry.get('roman_aspect_personality'),
                    'roman_only': entry.get('roman_only', False),
                    'home': entry.get('home'),
                    'description': entry.get('description'),
                }
                if entry.get('wiki_url'):
                    defaults['wiki_url'] = entry['wiki_url']

                first_book_slug = entry.get('first_appearance_book_slug')
                if first_book_slug:
                    first_book = _get_book(first_book_slug, entry['name'], self.stdout, self.style)
                    if first_book:
                        defaults['first_appearance_book'] = first_book
                else:
                    defaults['first_appearance_book'] = None

                god, created = God.objects.update_or_create(name=entry['name'], defaults=defaults)

                # Missing M2M book slugs are warned and omitted; valid references remain.
                if 'books_appeared_in_slugs' in entry:
                    books = [
                        book
                        for slug in entry['books_appeared_in_slugs']
                        if (book := _get_book(slug, entry['name'], self.stdout, self.style))
                    ]
                    god.books_appeared_in.set(books)

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created: {entry["name"]}'))
                else:
                    updated_count += 1
                    self.stdout.write(f'  Updated: {entry["name"]}')

            except (DatabaseError, ValidationError, KeyError, TypeError, ValueError) as exc:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  Failed:  {entry.get("name", "unknown")} — {exc}')
                )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Gods seeded: {created_count} created, '
                f'{updated_count} updated, '
                f'{error_count} errors.'
            )
        )
