"""Seed Monster records and book appearances from ``data/monsters.json``.

Character and God defeat relationships are managed separately and are not
seeded by this command.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from apps.bestiary.models import Monster
from apps.narrative.models import Book

DATA_FILE = settings.BASE_DIR / 'data' / 'monsters.json'


def _warn(stdout, style, message):
    stdout.write(style.WARNING(f'[WARN] {message}'))


def _resolve(model, slug, relation, monster_name, stdout, style):
    if not slug:
        return None
    try:
        return model.objects.get(slug=slug)
    except model.DoesNotExist:
        _warn(
            stdout,
            style,
            f"Unresolved {relation} '{slug}' for {monster_name} — leaving unset.",
        )
        return None


class Command(BaseCommand):
    help = 'Seed named Monsters from data/monsters.json.'

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
                first_book = _resolve(
                    Book,
                    entry.get('first_appearance_book_slug'),
                    'first appearance book',
                    name,
                    self.stdout,
                    self.style,
                )
                defaults = {
                    'slug': entry['expected_slug'],
                    'name': name,
                    'first_appearance_book': first_book,
                    **{
                        field: entry[field]
                        for field in (
                            'aliases',
                            'monster_type',
                            'allegiance',
                            'origin_myth',
                            'physical_description',
                            'abilities',
                            'weaknesses',
                            'notable_victims',
                            'can_reform',
                            'reform_time',
                            'reform_location',
                            'spoils_of_war',
                            'parent_entity',
                            'disguise_form',
                            'description',
                        )
                        if field in entry
                    },
                }
                if entry.get('wiki_url'):
                    defaults['wiki_url'] = entry['wiki_url']

                monster, created = Monster.objects.update_or_create(
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
                monster.books_appeared_in.set(books)

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
                f'Monsters seeded: {created_count} created, '
                f'{updated_count} updated, {error_count} errors.'
            )
        )
