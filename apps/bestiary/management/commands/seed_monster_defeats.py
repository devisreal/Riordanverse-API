"""Seed MonsterDefeat events from ``data/monster_defeats.json``.

Monsters, Characters, and Books should be seeded first. Missing required
Monster or Character references warn and skip that event. Missing optional
Book references warn and are stored as null.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from apps.bestiary.models import Monster, MonsterDefeat
from apps.characters.models import Character
from apps.narrative.models import Book

DATA_FILE = settings.BASE_DIR / 'data' / 'monster_defeats.json'


def _resolve(model, slug, relation, event_label, stdout, style, *, required=False):
    if not slug:
        if required:
            stdout.write(
                style.WARNING(f'[WARN] Missing {relation} for {event_label} — skipping event.')
            )
        return None
    try:
        return model.objects.get(slug=slug)
    except model.DoesNotExist:
        action = 'skipping event' if required else 'leaving unset'
        stdout.write(
            style.WARNING(f"[WARN] Unresolved {relation} '{slug}' for {event_label} — {action}.")
        )
        return None


class Command(BaseCommand):
    help = 'Seed MonsterDefeat events from data/monster_defeats.json.'

    def handle(self, *args, **kwargs):
        if not DATA_FILE.exists():
            self.stdout.write(self.style.ERROR(f'Data file not found: {DATA_FILE}'))
            return

        with DATA_FILE.open(encoding='utf-8') as data_file:
            entries = json.load(data_file)

        created_count = 0
        existing_count = 0
        skipped_count = 0
        error_count = 0

        for entry in entries:
            monster_slug = entry.get('monster_slug')
            character_slug = entry.get('defeated_by_slug')
            event_label = (
                f'{monster_slug or "unknown monster"} / {character_slug or "unknown Character"}'
            )

            try:
                monster = _resolve(
                    Monster,
                    monster_slug,
                    'Monster',
                    event_label,
                    self.stdout,
                    self.style,
                    required=True,
                )
                character = _resolve(
                    Character,
                    character_slug,
                    'Character',
                    event_label,
                    self.stdout,
                    self.style,
                    required=True,
                )
                if monster is None or character is None:
                    skipped_count += 1
                    continue

                book = _resolve(
                    Book,
                    entry.get('book_slug'),
                    'book',
                    event_label,
                    self.stdout,
                    self.style,
                )
                _, created = MonsterDefeat.objects.get_or_create(
                    monster=monster,
                    defeated_by=character,
                    book=book,
                    method=entry.get('method'),
                    is_myth=entry.get('is_myth', False),
                )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created: {event_label}'))
                else:
                    existing_count += 1
                    self.stdout.write(f'  Existing: {event_label}')
            except (DatabaseError, KeyError, TypeError, ValueError) as exc:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'  Failed: {event_label} — {exc}'))

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Monster defeats: {created_count} created, {existing_count} existing, '
                f'{skipped_count} skipped, {error_count} errors.'
            )
        )
