"""Seed Camp Half-Blood Cabin records from ``data/cabins.json``."""

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError, transaction

from apps.characters.models import Character
from apps.divinities.models import God
from apps.narrative.models import Book
from apps.organizations.models import Cabin

DATA_FILE = settings.BASE_DIR / 'data' / 'cabins.json'


def _resolve(model, slug, relation, cabin_number, stdout, style):
    if not slug:
        return None
    try:
        return model.objects.get(slug=slug)
    except model.DoesNotExist:
        stdout.write(
            style.WARNING(
                f"[WARN] Unresolved {relation} '{slug}' for Cabin {cabin_number} — skipping reference."
            )
        )
        return None


class Command(BaseCommand):
    help = 'Seed Camp Half-Blood cabins from data/cabins.json.'

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
            number = entry.get('number', '?')
            try:
                with transaction.atomic():
                    defaults = {
                        'slug': entry['expected_slug'],
                        'is_honorary': entry['is_honorary'],
                        'is_empty': entry['is_empty'],
                        'architecture_description': entry.get('architecture_description'),
                        'position': entry.get('position'),
                        'deity': _resolve(
                            God,
                            entry.get('deity_slug'),
                            'deity',
                            number,
                            self.stdout,
                            self.style,
                        ),
                        'head_counselor': _resolve(
                            Character,
                            entry.get('head_counselor_slug'),
                            'head counselor',
                            number,
                            self.stdout,
                            self.style,
                        ),
                        'added_in_book': _resolve(
                            Book,
                            entry.get('added_in_book_slug'),
                            'book',
                            number,
                            self.stdout,
                            self.style,
                        ),
                    }
                    cabin, created = Cabin.objects.update_or_create(
                        number=entry['number'],
                        defaults=defaults,
                    )

                    campers = []
                    for slug in entry.get('known_camper_slugs', []):
                        camper = _resolve(
                            Character,
                            slug,
                            'known camper',
                            number,
                            self.stdout,
                            self.style,
                        )
                        if camper is not None:
                            campers.append(camper)
                    cabin.known_campers.set(campers)

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created: Cabin {number}'))
                else:
                    updated_count += 1
                    self.stdout.write(f'  Updated: Cabin {number}')
            except (DatabaseError, KeyError, TypeError, ValueError) as exc:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'  Failed: Cabin {number} — {exc}'))

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Cabins seeded: {created_count} created, '
                f'{updated_count} updated, {error_count} errors.'
            )
        )
