"""Seed DivineRelationship records from ``data/divine_relationships.json``.

Re-run safe: immutable relationship tuples are created with ``get_or_create``.
Books, Gods, Titans, Characters, and Weapons should be seeded first. The
command also synchronizes God children/weapons and Titan weapons from their
seed files. Missing slugs warn and skip only the affected link.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError
from django.db.models import Q

from apps.characters.models import Character
from apps.divinities.models import DivineRelationship, God, Titan
from apps.items.models import Weapon

DATA_FILE = settings.BASE_DIR / 'data' / 'divine_relationships.json'
GODS_FILE = settings.BASE_DIR / 'data' / 'gods.json'
TITANS_FILE = settings.BASE_DIR / 'data' / 'titans.json'

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

        sibling_count = self._sync_sibling_links()
        direct_link_count = self._sync_direct_links()

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Divine relationships seeded: {created_count} created, '
                f'{skipped_count} already existed or skipped, {error_count} errors.'
            )
        )
        self.stdout.write(self.style.SUCCESS(f'Sibling links synchronized: {sibling_count}.'))
        self.stdout.write(
            self.style.SUCCESS(f'Direct divine links synchronized: {direct_link_count}.')
        )

    def _sync_sibling_links(self):
        """Create one typed DivineRelationship tuple for every source sibling pair."""
        synchronized_count = 0
        seen_pairs = set()
        for path, entity_type, entity_model in (
            (GODS_FILE, 'god', God),
            (TITANS_FILE, 'titan', Titan),
        ):
            if not path.exists():
                continue
            with path.open(encoding='utf-8') as data_file:
                entries = json.load(data_file)
            for entry in entries:
                try:
                    source = entity_model.objects.get(slug=entry['expected_slug'])
                except entity_model.DoesNotExist, KeyError:
                    continue
                for sibling_slug in entry.get('siblings', []):
                    sibling = God.objects.filter(slug=sibling_slug).first()
                    sibling_type = 'god'
                    if sibling is None:
                        sibling = Titan.objects.filter(slug=sibling_slug).first()
                        sibling_type = 'titan'
                    if sibling is None:
                        self.stdout.write(
                            self.style.WARNING(
                                f"[WARN] Unresolved sibling '{sibling_slug}' for "
                                f'{entity_type} {source.slug} — skipping link.'
                            )
                        )
                        continue

                    pair = tuple(sorted(((entity_type, source.slug), (sibling_type, sibling.slug))))
                    if pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)

                    forward = {
                        **_endpoint_kwargs('from', entity_type, source),
                        **_endpoint_kwargs('to', sibling_type, sibling),
                        'relationship_type': 'sibling_of',
                    }
                    reverse = {
                        **_endpoint_kwargs('from', sibling_type, sibling),
                        **_endpoint_kwargs('to', entity_type, source),
                        'relationship_type': 'sibling_of',
                    }
                    if DivineRelationship.objects.filter(Q(**forward) | Q(**reverse)).exists():
                        continue

                    _, created = DivineRelationship.objects.get_or_create(**forward)
                    synchronized_count += int(created)
        return synchronized_count

    def _sync_direct_links(self):
        """Synchronize source-declared God children/weapons and Titan weapons."""
        synced_count = 0
        for path, entity_model, relation_fields in (
            (
                GODS_FILE,
                God,
                {
                    'children_demigod_slugs': (Character, 'children_demigods'),
                    'weapon_slugs': (Weapon, 'weapons'),
                },
            ),
            (TITANS_FILE, Titan, {'weapon_slugs': (Weapon, 'weapons')}),
        ):
            if not path.exists():
                self.stdout.write(self.style.WARNING(f'[WARN] Data file not found: {path}'))
                continue
            with path.open(encoding='utf-8') as data_file:
                entries = json.load(data_file)
            for entry in entries:
                try:
                    entity = entity_model.objects.get(slug=entry['expected_slug'])
                except entity_model.DoesNotExist, KeyError:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[WARN] Unresolved {entity_model.__name__.lower()} '
                            f"'{entry.get('expected_slug', '?')}' — skipping direct links."
                        )
                    )
                    continue

                for source_field, (related_model, relation_name) in relation_fields.items():
                    if source_field not in entry:
                        continue
                    related_objects = []
                    for slug in entry[source_field]:
                        try:
                            related_objects.append(related_model.objects.get(slug=slug))
                        except related_model.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'[WARN] Unresolved {related_model.__name__.lower()} '
                                    f"'{slug}' in {entity_model.__name__.lower()} "
                                    f"'{entity.slug}' {source_field} — skipping link."
                                )
                            )
                    getattr(entity, relation_name).set(related_objects)
                    synced_count += len(related_objects)
        return synced_count
