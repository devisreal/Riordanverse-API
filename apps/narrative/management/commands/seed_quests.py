"""Seed Quest records and typed participants/casualties from ``data/quests.json``.

Books, prophecies, Characters, Gods, Titans, Monsters, Locations, and items
should be seeded first. Missing references warn and are skipped or set null.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from apps.bestiary.models import Monster
from apps.characters.models import Character
from apps.divinities.models import God, Titan
from apps.items.models import Weapon
from apps.locations.models import Location
from apps.narrative.models import (
    Book,
    Prophecy,
    Quest,
    QuestCasualty,
    QuestParticipant,
)

DATA_FILE = settings.BASE_DIR / 'data' / 'quests.json'

ENTITY_MODELS = {
    'character': Character,
    'god': God,
    'titan': Titan,
    'monster': Monster,
}

LINK_CONFIG = {
    'participants': (QuestParticipant, 'participant'),
    'casualties': (QuestCasualty, 'casualty'),
}


def _resolve(model, slug, relation, quest_title, stdout, style):
    if not slug:
        return None
    try:
        return model.objects.get(slug=slug)
    except model.DoesNotExist:
        stdout.write(
            style.WARNING(
                f"[WARN] Unresolved {relation} '{slug}' for {quest_title} — skipping reference."
            )
        )
        return None


def _sync_typed_links(quest, references, model, prefix, title, stdout, style):
    desired = {}
    for reference in references:
        entity_type = reference.get('type')
        entity_model = ENTITY_MODELS.get(entity_type)
        if entity_model is None:
            stdout.write(
                style.WARNING(
                    f"[WARN] Unknown {prefix} entity type '{entity_type}' for {title} — skipping."
                )
            )
            continue
        slug = reference.get('slug')
        entity = _resolve(entity_model, slug, f'{prefix} {entity_type}', title, stdout, style)
        if entity is not None:
            desired[(entity_type, entity.pk)] = entity

    current = list(
        model.objects.filter(quest=quest).select_related(
            f'{prefix}_character',
            f'{prefix}_god',
            f'{prefix}_titan',
            f'{prefix}_monster',
        )
    )
    for link in current:
        current_type = next(
            (
                entity_type
                for entity_type in ENTITY_MODELS
                if getattr(link, f'{prefix}_{entity_type}_id') is not None
            ),
            None,
        )
        current_entity = getattr(link, f'{prefix}_{current_type}') if current_type else None
        if current_type is None or (current_type, current_entity.pk) not in desired:
            link.delete()

    for (entity_type, _), entity in desired.items():
        model.objects.get_or_create(quest=quest, **{f'{prefix}_{entity_type}': entity})


class Command(BaseCommand):
    help = 'Seed quests from data/quests.json.'

    def handle(self, *args, **kwargs):
        if not DATA_FILE.exists():
            raise CommandError(f'Quest data file not found: {DATA_FILE}')

        with DATA_FILE.open(encoding='utf-8') as data_file:
            entries = json.load(data_file)
        if not isinstance(entries, list):
            raise CommandError('Quest data must be a JSON list.')

        created_count = 0
        updated_count = 0
        error_count = 0

        for entry in entries:
            title = entry.get('title', 'unknown')
            try:
                with transaction.atomic():
                    defaults = {
                        'title': title,
                        'book': _resolve(
                            Book, entry.get('book_slug'), 'book', title, self.stdout, self.style
                        ),
                        'prophecy': _resolve(
                            Prophecy,
                            entry.get('prophecy_slug'),
                            'prophecy',
                            title,
                            self.stdout,
                            self.style,
                        ),
                        'led_by': _resolve(
                            Character,
                            entry.get('led_by_slug'),
                            'quest leader',
                            title,
                            self.stdout,
                            self.style,
                        ),
                        'objective': entry.get('objective'),
                        'outcome': entry.get('outcome'),
                        'initiated_by': entry.get('initiated_by'),
                        'description': entry.get('description'),
                    }
                    if entry.get('wiki_url'):
                        defaults['wiki_url'] = entry['wiki_url']
                    quest, created = Quest.all_objects.update_or_create(
                        slug=entry['expected_slug'],
                        defaults=defaults,
                    )

                    for relation_name, model, model_class in (
                        ('locations', Location, 'locations_visited'),
                        ('monsters', Monster, 'monsters_encountered'),
                        ('items', Weapon, 'items_recovered'),
                    ):
                        resolved = []
                        for slug in entry.get(f'{relation_name[:-1]}_slugs', []):
                            entity = _resolve(
                                model,
                                slug,
                                relation_name[:-1],
                                title,
                                self.stdout,
                                self.style,
                            )
                            if entity is not None:
                                resolved.append(entity)
                        getattr(quest, model_class).set(resolved)

                    for relation_name, (link_model, prefix) in LINK_CONFIG.items():
                        _sync_typed_links(
                            quest,
                            entry.get(relation_name, []),
                            link_model,
                            prefix,
                            title,
                            self.stdout,
                            self.style,
                        )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created: {title}'))
                else:
                    updated_count += 1
                    self.stdout.write(f'  Updated: {title}')
            except (DatabaseError, KeyError, TypeError, ValueError) as exc:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'  Failed: {title} — {exc}'))

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Quests seeded: {created_count} created, '
                f'{updated_count} updated, {error_count} errors.'
            )
        )
