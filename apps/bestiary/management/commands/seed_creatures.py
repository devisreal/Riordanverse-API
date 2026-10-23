"""Seed creature species and typed Character/Monster members from ``data/creatures.json``.

Characters and Monsters should be seeded first. Missing member references warn
and are skipped rather than aborting the command.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from apps.bestiary.models import Creature, CreatureMember, Monster
from apps.characters.models import Character

DATA_FILE = settings.BASE_DIR / 'data' / 'creatures.json'
ENTITY_MODELS = {'character': Character, 'monster': Monster}


def _resolve_member(entity_type, slug, creature_name, stdout, style):
    model = ENTITY_MODELS.get(entity_type)
    if model is None:
        stdout.write(
            style.WARNING(
                f"[WARN] Unknown Creature member type '{entity_type}' for {creature_name} — skipping."
            )
        )
        return None
    if not slug:
        stdout.write(
            style.WARNING(
                f'[WARN] Missing {entity_type} member slug for {creature_name} — skipping.'
            )
        )
        return None
    try:
        return model.objects.get(slug=slug)
    except model.DoesNotExist:
        stdout.write(
            style.WARNING(
                f"[WARN] Unresolved {entity_type} member '{slug}' for {creature_name} "
                '— skipping reference.'
            )
        )
        return None


def _sync_members(creature, references, stdout, style):
    desired = {}
    for reference in references:
        entity_type = reference.get('type')
        entity = _resolve_member(
            entity_type,
            reference.get('slug'),
            creature.name,
            stdout,
            style,
        )
        if entity is not None:
            desired[(entity_type, entity.pk)] = entity

    current = list(
        CreatureMember.objects.filter(creature=creature).select_related(
            'member_character', 'member_monster'
        )
    )
    for link in current:
        if link.member_character_id:
            current_type, entity = 'character', link.member_character
        elif link.member_monster_id:
            current_type, entity = 'monster', link.member_monster
        else:
            link.delete()
            continue
        if (current_type, entity.pk) not in desired:
            link.delete()

    for (entity_type, _), entity in desired.items():
        CreatureMember.objects.get_or_create(
            creature=creature,
            **{f'member_{entity_type}': entity},
        )


class Command(BaseCommand):
    help = 'Seed creature species and typed members from data/creatures.json.'

    def handle(self, *args, **kwargs):
        if not DATA_FILE.exists():
            raise CommandError(f'Creature data file not found: {DATA_FILE}')

        with DATA_FILE.open(encoding='utf-8') as data_file:
            entries = json.load(data_file)
        if not isinstance(entries, list):
            raise CommandError('Creature data must be a JSON list.')

        created_count = 0
        updated_count = 0
        error_count = 0

        for entry in entries:
            name = entry.get('name', 'unknown')
            try:
                with transaction.atomic():
                    defaults = {
                        field: entry.get(field)
                        for field in (
                            'name',
                            'description',
                            'origin',
                            'alignment',
                            'habitat',
                            'abilities',
                            'weaknesses',
                        )
                    }
                    if entry.get('wiki_url'):
                        defaults['wiki_url'] = entry['wiki_url']
                    creature, created = Creature.objects.update_or_create(
                        slug=entry['expected_slug'],
                        defaults=defaults,
                    )

                    references = entry.get('notable_members')
                    if references is None:
                        # Read legacy seed rows as Character-only member links.
                        references = [
                            {'type': 'character', 'slug': slug}
                            for slug in entry.get('notable_member_slugs', [])
                        ]
                    _sync_members(creature, references, self.stdout, self.style)

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
                f'Creatures seeded: {created_count} created, '
                f'{updated_count} updated, {error_count} errors.'
            )
        )
