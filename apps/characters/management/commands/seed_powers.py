"""Seed Character Power records from ``data/powers.json``.

Characters and Books should be seeded first. The supplied divine-parent slug
is validated against the Character's existing divine parent, not stored as a
duplicate relationship.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from apps.characters.models import Character, Power
from apps.divinities.models import DivineRelationship
from apps.narrative.models import Book

DATA_FILE = settings.BASE_DIR / 'data' / 'powers.json'


def _warning(stdout, style, message):
    stdout.write(style.WARNING(f'[WARN] {message}'))


def _resolve_book(slug, power_name, stdout, style):
    if not slug:
        return None
    try:
        return Book.objects.get(slug=slug)
    except Book.DoesNotExist:
        _warning(stdout, style, f"Unresolved book '{slug}' for {power_name} — leaving unset.")
        return None


class Command(BaseCommand):
    help = 'Seed character Powers from data/powers.json.'

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
            character_slug = entry.get('character_slug')
            try:
                try:
                    character = Character.objects.get(slug=character_slug)
                except Character.DoesNotExist:
                    _warning(
                        self.stdout,
                        self.style,
                        f"Unresolved character '{character_slug}' for {name} — skipping power.",
                    )
                    continue

                expected_parent_slug = entry.get('divine_parent_slug')
                if expected_parent_slug or entry.get('source') == 'divine_parent':
                    parent_relationships = DivineRelationship.objects.filter(
                        to_character=character,
                        relationship_type='parent_of',
                    )
                    actual_parent_slugs = set(
                        parent_relationships.filter(from_god__isnull=False).values_list(
                            'from_god__slug', flat=True
                        )
                    ) | set(
                        parent_relationships.filter(from_titan__isnull=False).values_list(
                            'from_titan__slug', flat=True
                        )
                    )
                    if expected_parent_slug and expected_parent_slug not in actual_parent_slugs:
                        _warning(
                            self.stdout,
                            self.style,
                            f"Divine-parent check failed for {character.name}'s {name}: "
                            f"seed says '{expected_parent_slug}', family links contain "
                            f'{sorted(actual_parent_slugs)}.',
                        )

                first_book = _resolve_book(
                    entry.get('first_demonstrated_book'),
                    name,
                    self.stdout,
                    self.style,
                )
                defaults = {
                    'type': entry.get('power_type', 'utility'),
                    'source': entry.get('source'),
                    'description': entry.get('description'),
                    'scope': entry.get('scope', []),
                    'limitations': entry.get('limitations'),
                    'is_passive': entry.get('is_passive', False),
                    'is_book_specific': entry.get('is_book_specific', False),
                    'first_demonstrated_book': first_book,
                    'display_order': entry.get('display_order', 0),
                }
                if entry.get('wiki_url'):
                    defaults['wiki_url'] = entry['wiki_url']

                _, created = Power.objects.update_or_create(
                    character=character,
                    name=name,
                    defaults=defaults,
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created: {character.name} — {name}'))
                else:
                    updated_count += 1
                    self.stdout.write(f'  Updated: {character.name} — {name}')
            except (DatabaseError, KeyError, TypeError, ValueError) as exc:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'  Failed: {name} — {exc}'))

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Powers seeded: {created_count} created, '
                f'{updated_count} updated, {error_count} errors.'
            )
        )
