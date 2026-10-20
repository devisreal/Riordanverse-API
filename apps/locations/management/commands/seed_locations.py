"""Seed Location records from ``data/locations.json``.

Books, Gods, Titans, Characters, and Monsters should be seeded first.
Unresolved controller references warn and are left null; unresolved book
references warn and are omitted.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from apps.bestiary.models import Monster
from apps.characters.models import Character
from apps.divinities.models import God, Titan
from apps.locations.models import Location
from apps.narrative.models import Book

DATA_FILE = settings.BASE_DIR / 'data' / 'locations.json'


def _resolve(model, slug, relation, location_name, stdout, style):
    if not slug:
        return None
    try:
        return model.objects.get(slug=slug)
    except model.DoesNotExist:
        stdout.write(
            style.WARNING(
                f"[WARN] Unresolved {relation} '{slug}' for {location_name} — leaving unset."
            )
        )
        return None


class Command(BaseCommand):
    help = 'Seed locations from data/locations.json.'

    def handle(self, *args, **kwargs):
        if not DATA_FILE.exists():
            self.stdout.write(self.style.ERROR(f'Data file not found: {DATA_FILE}'))
            return

        with DATA_FILE.open(encoding='utf-8') as data_file:
            entries = json.load(data_file)

        created_count = 0
        updated_count = 0
        error_count = 0

        for entry in entries:
            name = entry.get('name', 'unknown')
            try:
                defaults = {
                    'slug': entry['expected_slug'],
                    'name': name,
                    **{
                        field: entry[field]
                        for field in (
                            'location_type',
                            'real_world_location',
                            'mythological_significance',
                            'is_hidden_from_mortals',
                            'coordinates_approx',
                            'notable_events',
                            'description',
                        )
                        if field in entry
                    },
                }
                for model, slug_field, relation, target_field in (
                    (God, 'controlled_by_god_slug', 'God controller', 'controlled_by_god'),
                    (
                        Titan,
                        'controlled_by_titan_slug',
                        'Titan controller',
                        'controlled_by_titan',
                    ),
                    (
                        Character,
                        'controlled_by_character_slug',
                        'Character controller',
                        'controlled_by_character',
                    ),
                    (
                        Monster,
                        'controlled_by_monster_slug',
                        'Monster controller',
                        'controlled_by_monster',
                    ),
                ):
                    defaults[target_field] = _resolve(
                        model,
                        entry.get(slug_field),
                        relation,
                        name,
                        self.stdout,
                        self.style,
                    )

                location, created = Location.objects.update_or_create(
                    slug=entry['expected_slug'],
                    defaults=defaults,
                )

                books = []
                for slug in entry.get('books_appeared_in_slugs', []):
                    book = _resolve(
                        Book,
                        slug,
                        'book appearance',
                        name,
                        self.stdout,
                        self.style,
                    )
                    if book is not None:
                        books.append(book)
                location.books_appeared_in.set(books)

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created: {name}'))
                else:
                    updated_count += 1
                    self.stdout.write(f'  Updated: {name}')
            except (DatabaseError, KeyError, TypeError, ValueError) as exc:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'  Failed: {name} — {exc}'))

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Locations seeded: {created_count} created, '
                f'{updated_count} updated, {error_count} errors.'
            )
        )
