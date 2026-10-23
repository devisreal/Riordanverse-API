"""Seed Event records and typed casualties from ``data/events.json``.

Books, Locations, Characters, Gods, Titans, and Monsters should be seeded
first. Missing foreign-key and entity references warn and are skipped or set
null rather than aborting the command.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from apps.bestiary.models import Monster
from apps.characters.models import Character
from apps.divinities.models import God, Titan
from apps.locations.models import Location
from apps.narrative.models import Book, Event, EventCasualty

DATA_FILE = settings.BASE_DIR / 'data' / 'events.json'

ENTITY_MODELS = {
    'character': Character,
    'god': God,
    'titan': Titan,
    'monster': Monster,
}
PARTICIPANT_RELATIONS = {
    'character': 'participant_characters',
    'god': 'participant_gods',
    'titan': 'participant_titans',
    'monster': 'participant_monsters',
}


def _resolve(model, slug, relation, event_name, stdout, style):
    if not slug:
        return None
    try:
        return model.objects.get(slug=slug)
    except model.DoesNotExist:
        stdout.write(
            style.WARNING(
                f"[WARN] Unresolved {relation} '{slug}' for {event_name} — skipping reference."
            )
        )
        return None


def _sync_casualties(event, references, stdout, style):
    desired = {}
    for reference in references:
        entity_type = reference.get('type')
        model = ENTITY_MODELS.get(entity_type)
        if model is None:
            stdout.write(
                style.WARNING(
                    f"[WARN] Unknown casualty entity type '{entity_type}' for {event.name} — skipping."
                )
            )
            continue
        entity = _resolve(
            model,
            reference.get('slug'),
            f'{entity_type} casualty',
            event.name,
            stdout,
            style,
        )
        if entity is not None:
            desired[(entity_type, entity.pk)] = entity

    current = list(
        EventCasualty.objects.filter(event=event).select_related(
            'casualty_character',
            'casualty_god',
            'casualty_titan',
            'casualty_monster',
        )
    )
    for link in current:
        current_type = next(
            (
                entity_type
                for entity_type in ENTITY_MODELS
                if getattr(link, f'casualty_{entity_type}_id') is not None
            ),
            None,
        )
        entity = getattr(link, f'casualty_{current_type}') if current_type else None
        if current_type is None or (current_type, entity.pk) not in desired:
            link.delete()

    for (entity_type, _), entity in desired.items():
        EventCasualty.objects.get_or_create(event=event, **{f'casualty_{entity_type}': entity})


class Command(BaseCommand):
    help = 'Seed lore events from data/events.json.'

    def handle(self, *args, **kwargs):
        if not DATA_FILE.exists():
            raise CommandError(f'Event data file not found: {DATA_FILE}')

        with DATA_FILE.open(encoding='utf-8') as data_file:
            entries = json.load(data_file)
        if not isinstance(entries, list):
            raise CommandError('Event data must be a JSON list.')

        created_count = 0
        updated_count = 0
        error_count = 0

        for entry in entries:
            name = entry.get('name', 'unknown')
            try:
                with transaction.atomic():
                    defaults = {
                        'name': name,
                        'event_type': entry['event_type'],
                        'book': _resolve(
                            Book,
                            entry.get('book_slug'),
                            'book',
                            name,
                            self.stdout,
                            self.style,
                        ),
                        'location': _resolve(
                            Location,
                            entry.get('location_slug'),
                            'location',
                            name,
                            self.stdout,
                            self.style,
                        ),
                        'outcome': entry.get('outcome'),
                        'significance': entry.get('significance'),
                        'description': entry.get('description'),
                    }
                    if entry.get('wiki_url'):
                        defaults['wiki_url'] = entry['wiki_url']
                    event, created = Event.objects.update_or_create(
                        slug=entry['expected_slug'],
                        defaults=defaults,
                    )

                    desired_participants = {entity_type: [] for entity_type in ENTITY_MODELS}
                    for reference in entry.get('participants', []):
                        entity_type = reference.get('type')
                        model = ENTITY_MODELS.get(entity_type)
                        if model is None:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"[WARN] Unknown participant entity type '{entity_type}' "
                                    f'for {name} — skipping.'
                                )
                            )
                            continue
                        entity = _resolve(
                            model,
                            reference.get('slug'),
                            f'{entity_type} participant',
                            name,
                            self.stdout,
                            self.style,
                        )
                        if entity is not None:
                            desired_participants[entity_type].append(entity)

                    for entity_type, relation in PARTICIPANT_RELATIONS.items():
                        getattr(event, relation).set(desired_participants[entity_type])

                    _sync_casualties(
                        event,
                        entry.get('casualties', []),
                        self.stdout,
                        self.style,
                    )

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
                f'Events seeded: {created_count} created, '
                f'{updated_count} updated, {error_count} errors.'
            )
        )
