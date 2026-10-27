"""Seed unified DivineRelationship family tuples from ``data/family_relationships.json``.

Re-run safe: immutable relationship tuples are created with ``get_or_create``.
All entity and Book seed commands should run first. Missing slugs warn and skip
only the affected link; God/Titan weapon links remain synchronized separately.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError
from django.db.models import Q

from apps.bestiary.models import Creature, Monster
from apps.characters.models import Character
from apps.divinities.models import RELATIONSHIP_ENTITY_TYPES, DivineRelationship, God, Titan
from apps.items.models import Weapon

DATA_FILE = settings.BASE_DIR / 'data' / 'family_relationships.json'
GODS_FILE = settings.BASE_DIR / 'data' / 'gods.json'
TITANS_FILE = settings.BASE_DIR / 'data' / 'titans.json'

ENTITY_MODELS = {
    'god': God,
    'titan': Titan,
    'character': Character,
    'monster': Monster,
    'creature': Creature,
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
    return {
        f'{side}_{kind}': entity if kind == entity_type else None
        for kind in RELATIONSHIP_ENTITY_TYPES
    }


class Command(BaseCommand):
    help = 'Seed immutable family relationship tuples from data/family_relationships.json.'

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
                if relationship_type not in ('parent_of', 'child_of', 'sibling_of', 'consort_of'):
                    self.stdout.write(
                        self.style.WARNING(
                            f"[WARN] Unknown relationship type '{relationship_type}' — skipping link."
                        )
                    )
                    skipped_count += 1
                    continue
                if relationship_type == 'child_of':
                    from_type, to_type = to_type, from_type
                    from_slug, to_slug = to_slug, from_slug
                    relationship_type = 'parent_of'

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

        direct_link_count = self._sync_direct_links()
        direct_link_count += self._sync_character_relationships()

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Divine relationships seeded: {created_count} created, '
                f'{skipped_count} already existed or skipped, {error_count} errors.'
            )
        )
        self.stdout.write(self.style.SUCCESS(f'Weapon links synchronized: {direct_link_count}.'))

    def _sync_direct_links(self):
        """Project God children and synchronize God/Titan weapon references."""
        synced_count = 0
        for path, entity_model, relation_fields in (
            (
                GODS_FILE,
                God,
                {'weapon_slugs': (Weapon, 'weapons')},
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
        for god in God.objects.all():
            children = Character.objects.filter(
                divine_relationships_as_to__from_god=god,
                divine_relationships_as_to__relationship_type='parent_of',
            ).distinct()
            god.children_demigods.set(children)
            synced_count += children.count()
        return synced_count

    def _sync_character_relationships(self):
        """Keep legacy Character parent/sibling fields projected from the graph."""
        synced_count = 0
        for character in Character.objects.all():
            parent_relationships = list(
                DivineRelationship.objects.filter(
                    to_character=character,
                    relationship_type='parent_of',
                ).select_related('from_god', 'from_titan', 'from_character')
            )
            god_parents = [
                relationship.from_god
                for relationship in parent_relationships
                if relationship.from_god_id
            ]
            titan_parents = [
                relationship.from_titan
                for relationship in parent_relationships
                if relationship.from_titan_id
            ]
            mortal_parents = [
                relationship.from_character
                for relationship in parent_relationships
                if relationship.from_character_id
            ]

            desired_god_parent = (
                god_parents[0] if len(god_parents) == 1 and not titan_parents else None
            )
            desired_titan_parent = (
                titan_parents[0] if len(titan_parents) == 1 and not god_parents else None
            )
            desired_mortal_parent = mortal_parents[0] if len(mortal_parents) == 1 else None
            changed_fields = []
            if character.divine_parent_id != getattr(desired_god_parent, 'pk', None):
                character.divine_parent = desired_god_parent
                changed_fields.append('divine_parent')
            if character.divine_parent_titan_id != getattr(desired_titan_parent, 'pk', None):
                character.divine_parent_titan = desired_titan_parent
                changed_fields.append('divine_parent_titan')
            if character.mortal_parent_ref_id != getattr(desired_mortal_parent, 'pk', None):
                character.mortal_parent_ref = desired_mortal_parent
                changed_fields.append('mortal_parent_ref')
            if desired_mortal_parent and not character.mortal_parent_name:
                character.mortal_parent_name = desired_mortal_parent.name
                changed_fields.append('mortal_parent_name')
            if changed_fields:
                character.save(update_fields=changed_fields)
                synced_count += 1

            sibling_relationships = (
                DivineRelationship.objects.filter(
                    relationship_type='sibling_of',
                )
                .filter(Q(from_character=character) | Q(to_character=character))
                .select_related('from_character', 'to_character')
            )
            siblings = []
            for relationship in sibling_relationships:
                sibling = (
                    relationship.to_character
                    if relationship.from_character_id == character.pk
                    else relationship.from_character
                )
                if sibling and sibling.pk != character.pk:
                    siblings.append(sibling)
            if set(character.siblings.values_list('pk', flat=True)) != {
                sibling.pk for sibling in siblings
            }:
                character.siblings.set(siblings)
                synced_count += len(siblings)
        return synced_count
