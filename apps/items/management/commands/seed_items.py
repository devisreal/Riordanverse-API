"""Seed weapon and magical-item records from ``data/weapons.json``.

Books, Gods, Titans, and Characters should be seeded first. Unresolved
foreign-key references warn and are left null; missing book references warn
and are skipped.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from apps.characters.models import Character
from apps.divinities.models import God, Titan
from apps.items.models import Weapon
from apps.narrative.models import Book

DATA_FILE = settings.BASE_DIR / 'data' / 'weapons.json'


def _resolve(model, slug, relation_name, weapon_name, stdout, style):
    if not slug:
        return None
    try:
        return model.objects.get(slug=slug)
    except model.DoesNotExist:
        stdout.write(
            style.WARNING(
                f"[WARN] Unresolved {relation_name} '{slug}' for {weapon_name} — leaving unset."
            )
        )
        return None


class Command(BaseCommand):
    help = 'Seed items (weapons and magical items) from data/weapons.json.'

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
                    **{
                        field: entry[field]
                        for field in (
                            'true_name',
                            'weapon_type',
                            'material',
                            'form',
                            'abilities',
                            'transforms',
                            'transform_trigger',
                            'passes_through_mortals',
                            'owner_history',
                            'forged_by_notes',
                            'origin_story',
                            'description',
                        )
                        if field in entry
                    },
                }
                if entry.get('wiki_url'):
                    defaults['wiki_url'] = entry['wiki_url']

                defaults['owner_primary_character'] = _resolve(
                    Character,
                    entry.get('owner_primary_character_slug'),
                    'character owner',
                    name,
                    self.stdout,
                    self.style,
                )
                defaults['owner_primary_god'] = _resolve(
                    God,
                    entry.get('owner_primary_god_slug'),
                    'God owner',
                    name,
                    self.stdout,
                    self.style,
                )
                defaults['owner_primary_titan'] = _resolve(
                    Titan,
                    entry.get('owner_primary_titan_slug'),
                    'Titan owner',
                    name,
                    self.stdout,
                    self.style,
                )
                defaults['forged_by'] = _resolve(
                    God,
                    entry.get('forged_by_god_slug'),
                    'God forger',
                    name,
                    self.stdout,
                    self.style,
                )
                defaults['forged_by_character'] = _resolve(
                    Character,
                    entry.get('forged_by_character_slug'),
                    'character forger',
                    name,
                    self.stdout,
                    self.style,
                )

                first_book_slug = entry.get('first_appearance_book_slug')
                defaults['first_appearance_book'] = _resolve(
                    Book,
                    first_book_slug,
                    'first appearance book',
                    name,
                    self.stdout,
                    self.style,
                )

                weapon, created = Weapon.objects.update_or_create(
                    name=name,
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
                weapon.books_appeared_in.set(books)

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
                f'Weapons seeded: {created_count} created, '
                f'{updated_count} updated, {error_count} errors.'
            )
        )
