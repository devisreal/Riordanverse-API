"""
Management command: seed_divine_relationships
Loads all V1 DivineRelationship records from data/divine_relationships.json.

Re-run safe: uses get_or_create on the full relationship tuple to avoid
duplicate rows. The UniqueConstraint on the model enforces this at the
DB level as a backup.

Dependency order:
- seed_gods must run first
- seed_titans must run first

JSON format expected per record:
    {
        "from_type": "god" | "titan",
        "from_slug": "<slug>",
        "to_type": "god" | "titan",
        "to_slug": "<slug>",
        "relationship_type": "parent_of" | "child_of" | "sibling_of" | "consort_of"
    }

Note on sibling_of and consort_of directionality:
    These are stored as a single directed row (A → sibling_of → B).
    The serializer reads both relationships_as_from and relationships_as_to
    to present a complete picture on each entity. Do NOT add reverse rows
    (B → sibling_of → A) — they duplicate the same semantic relationship.
"""

import json

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from apps.divinities.models import DivineRelationship, God, Titan

DATA_FILE = settings.BASE_DIR / 'data' / 'divine_relationships.json'


def _resolve_entity(entity_type, slug):
    """
    Resolve a from/to entity by type and slug.
    Returns (god_instance, None) or (None, titan_instance).
    Returns (None, None) and logs a warning if not found.
    """
    if entity_type == 'god':
        try:
            return God.objects.get(slug=slug), None
        except God.DoesNotExist:
            return None, None
    elif entity_type == 'titan':
        try:
            return None, Titan.objects.get(slug=slug)
        except Titan.DoesNotExist:
            return None, None
    return None, None


class Command(BaseCommand):
    help = 'Seed V1 DivineRelationship records from data/divine_relationships.json'

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

                from_god, from_titan = _resolve_entity(from_type, from_slug)
                to_god, to_titan = _resolve_entity(to_type, to_slug)

                # Validate both sides resolved
                if from_type == 'god' and from_god is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Skipped: God '{from_slug}' not found "
                            f'(from side of {relationship_type})'
                        )
                    )
                    error_count += 1
                    continue

                if from_type == 'titan' and from_titan is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Skipped: Titan '{from_slug}' not found "
                            f'(from side of {relationship_type})'
                        )
                    )
                    error_count += 1
                    continue

                if to_type == 'god' and to_god is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Skipped: God '{to_slug}' not found (to side of {relationship_type})"
                        )
                    )
                    error_count += 1
                    continue

                if to_type == 'titan' and to_titan is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Skipped: Titan '{to_slug}' not found "
                            f'(to side of {relationship_type})'
                        )
                    )
                    error_count += 1
                    continue

                _, created = DivineRelationship.objects.get_or_create(
                    from_god=from_god,
                    from_titan=from_titan,
                    to_god=to_god,
                    to_titan=to_titan,
                    relationship_type=relationship_type,
                )

                label = f'{from_type}:{from_slug} → {relationship_type} → {to_type}:{to_slug}'

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created: {label}'))
                else:
                    skipped_count += 1
                    self.stdout.write(f'  Exists:  {label}')

            except (DatabaseError, ValidationError, KeyError, TypeError, ValueError) as exc:
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
                f'{skipped_count} already existed, '
                f'{error_count} errors/skipped.'
            )
        )
