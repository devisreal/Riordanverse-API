"""
Management command: seed_titans
Loads all V1 Titan records from data/titans.json.

Re-run safe: uses update_or_create on name.

Dependency order:
- Books must be seeded first (seed_books) — references first_appearance_book
  and books_appeared_in by slug.
- Gods do not need to exist yet for titans — DivineRelationship
  handles cross-model links and is seeded separately by seed_divine_relationships.
"""

import json

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from apps.core.seed_utils import update_or_create_by_expected_slug
from apps.divinities.models import Titan
from apps.narrative.models import Book

DATA_FILE = settings.BASE_DIR / 'data' / 'titans.json'


def _get_book(slug, titan_name, stdout, style):
    """Resolve a book slug and emit a warning rather than failing the seed."""
    try:
        return Book.objects.get(slug=slug)
    except Book.DoesNotExist:
        stdout.write(
            style.WARNING(
                f"  Warning: Book '{slug}' not found for {titan_name} — skipping that reference."
            )
        )
        return None


class Command(BaseCommand):
    help = 'Seed V1 Titan records from data/titans.json'

    def handle(self, *args, **kwargs):
        if not DATA_FILE.exists():
            self.stdout.write(self.style.ERROR(f'Data file not found: {DATA_FILE}'))
            return

        with DATA_FILE.open(encoding='utf-8') as data_file:
            titans = json.load(data_file)

        created_count = 0
        updated_count = 0
        error_count = 0

        for entry in titans:
            try:
                defaults = {
                    'roman_name': entry.get('roman_name'),
                    'mythology': entry.get('mythology', 'greek'),
                    'generation': entry.get('generation', 'elder_titan'),
                    'display_order': entry.get('display_order'),
                    'status': entry.get('status', 'imprisoned'),
                    'alignment': entry.get('alignment', 'kronos_army'),
                    'domains': entry.get('domains', []),
                    'symbols': entry.get('symbols', []),
                    'sacred_animals': entry.get('sacred_animals', []),
                    'sacred_plants': entry.get('sacred_plants', []),
                    'weapon_or_power': entry.get('weapon_or_power', []),
                    'role_in_series': entry.get('role_in_series'),
                    'prison_location': entry.get('prison_location'),
                    'description': entry.get('description'),
                }
                if 'home' in entry:
                    defaults['home'] = entry['home']
                if entry.get('wiki_url'):
                    defaults['wiki_url'] = entry['wiki_url']

                first_book_slug = entry.get('first_appearance_book_slug')
                if first_book_slug:
                    first_book = _get_book(first_book_slug, entry['name'], self.stdout, self.style)
                    if first_book:
                        defaults['first_appearance_book'] = first_book
                else:
                    defaults['first_appearance_book'] = None

                expected_slug = entry.get('expected_slug')
                if expected_slug:
                    titan, created = update_or_create_by_expected_slug(
                        Titan,
                        expected_slug,
                        defaults,
                        fallback={'name': entry['name']},
                    )
                else:
                    titan, created = Titan.all_objects.update_or_create(
                        name=entry['name'], defaults=defaults
                    )

                # Missing M2M book slugs are warned and omitted; valid references remain.
                if 'books_appeared_in_slugs' in entry:
                    books = [
                        book
                        for slug in entry['books_appeared_in_slugs']
                        if (book := _get_book(slug, entry['name'], self.stdout, self.style))
                    ]
                    titan.books_appeared_in.set(books)

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
                f'Titans seeded: {created_count} created, '
                f'{updated_count} updated, '
                f'{error_count} errors.'
            )
        )
