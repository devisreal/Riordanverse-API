"""Seed DivineRelationship records from ``data/divine_relationships.json``.

Re-run safe: immutable relationship tuples are created with ``get_or_create``.
Books, Gods, Titans, and Characters should be seeded first. Missing endpoint
slugs warn and skip only the affected relationship.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from apps.characters.models import Character
from apps.divinities.models import DivineRelationship, God, Titan

DATA_FILE = settings.BASE_DIR / 'data' / 'divine_relationships.json'

ENTITY_MODELS = {
    'god': God,
    'titan': Titan,
    'character': Character,
}


def _resolve_entity(entity_type, slug):
    model = ENTITY_MODELS.get(entity_type)
    if model is None:
        return None
    try:
        return model.objects.get(slug=slug)
    except model.DoesNotExist:
        return None


def _endpoint_kwargs(side, entity_type, entity):
    return {f'{side}_{kind}': entity if kind == entity_type else None for kind in ENTITY_MODELS}


class Command(BaseCommand):
    help = 'Seed immutable divine relationship tuples from data/divine_relationships.json.'

    def handle(self, *args, **kwargs):
        if not DATA_FILE.exists():
            self.stdout.write(self.style.ERROR(f'Data file not found: {DATA_FILE}'))
            return

        with DATA_FILE.open(encoding='utf-8') as data_file:
            relationships = json.load(data_file)

        created_count = 0
        skipped_count = 0
        error_count = 0

        for entry in relationships:
            try:
                from_type = entry['from_type']
                from_slug = entry['from_slug']
                to_type = entry['to_type']
                to_slug = entry['to_slug']
                relationship_type = entry['relationship_type']

                from_entity = _resolve_entity(from_type, from_slug)
                to_entity = _resolve_entity(to_type, to_slug)
                missing = False
                if from_entity is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[WARN] Unresolved {from_type} '{from_slug}' — "
                            f'skipping {relationship_type} relationship.'
                        )
                    )
                    missing = True
                if to_entity is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[WARN] Unresolved {to_type} '{to_slug}' — "
                            f'skipping {relationship_type} relationship.'
                        )
                    )
                    missing = True
                if missing:
                    skipped_count += 1
                    continue

                endpoints = {
                    **_endpoint_kwargs('from', from_type, from_entity),
                    **_endpoint_kwargs('to', to_type, to_entity),
                }
                _, created = DivineRelationship.objects.get_or_create(
                    **endpoints,
                    relationship_type=relationship_type,
                )
                label = f'{from_type}:{from_slug} → {relationship_type} → {to_type}:{to_slug}'

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created: {label}'))
                else:
                    skipped_count += 1
                    self.stdout.write(f'  Exists:  {label}')

            except (DatabaseError, KeyError, TypeError, ValueError) as exc:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  Failed:  {entry.get("from_slug", "?")} → '
                        f'{entry.get("to_slug", "?")} — {exc}'
                    )
                )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Divine relationships seeded: {created_count} created, '
                f'{skipped_count} already existed or skipped, {error_count} errors.'
            )
        )
