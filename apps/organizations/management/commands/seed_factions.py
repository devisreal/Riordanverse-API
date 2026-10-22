"""Seed factions and typed membership links from ``data/factions.json``."""

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError, transaction

from apps.bestiary.models import Monster
from apps.characters.models import Character
from apps.divinities.models import God, Titan
from apps.narrative.models import Book
from apps.organizations.models import Faction, FactionMember

DATA_FILE = settings.BASE_DIR / 'data' / 'factions.json'

ENTITY_MODELS = {
    'character': Character,
    'god': God,
    'titan': Titan,
    'monster': Monster,
}


def _resolve(model, slug, relation, faction_name, stdout, style):
    if not slug:
        return None
    try:
        return model.objects.get(slug=slug)
    except model.DoesNotExist:
        stdout.write(
            style.WARNING(
                f"[WARN] Unresolved {relation} '{slug}' for {faction_name} — skipping reference."
            )
        )
        return None


class Command(BaseCommand):
    help = 'Seed factions from data/factions.json.'

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
            try:
                with transaction.atomic():
                    defaults = {
                        'name': name,
                        'faction_type': entry['faction_type'],
                        'alignment': entry['alignment'],
                        'description': entry.get('description'),
                        'leader_character': _resolve(
                            Character,
                            entry.get('leader_character_slug'),
                            'character leader',
                            name,
                            self.stdout,
                            self.style,
                        ),
                        'leader_god': _resolve(
                            God,
                            entry.get('leader_god_slug'),
                            'God leader',
                            name,
                            self.stdout,
                            self.style,
                        ),
                    }
                    if entry.get('wiki_url'):
                        defaults['wiki_url'] = entry['wiki_url']

                    faction, created = Faction.objects.update_or_create(
                        slug=entry['expected_slug'],
                        defaults=defaults,
                    )

                    desired_members = {}
                    for member_ref in entry.get('members', []):
                        member_type = member_ref.get('type')
                        model = ENTITY_MODELS.get(member_type)
                        if model is None:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"[WARN] Unknown member type '{member_type}' in {name} — skipping."
                                )
                            )
                            continue

                        slug = member_ref.get('slug')
                        entity = _resolve(
                            model,
                            slug,
                            f'{member_type} member',
                            name,
                            self.stdout,
                            self.style,
                        )
                        if entity is not None:
                            desired_members[(member_type, entity.pk)] = entity

                    current_members = list(faction.member_records.all())
                    for membership in current_members:
                        existing_member = next(
                            (
                                getattr(membership, f'member_{member_type}')
                                for member_type in ENTITY_MODELS
                                if getattr(membership, f'member_{member_type}_id') is not None
                            ),
                            None,
                        )
                        if existing_member is None:
                            membership.delete()
                            continue
                        existing_type = next(
                            member_type
                            for member_type in ENTITY_MODELS
                            if getattr(membership, f'member_{member_type}_id') is not None
                        )
                        if (existing_type, existing_member.pk) not in desired_members:
                            membership.delete()

                    for (member_type, _), entity in desired_members.items():
                        FactionMember.objects.get_or_create(
                            faction=faction,
                            **{f'member_{member_type}': entity},
                        )

                    books = []
                    for slug in entry.get('books_active_in_slugs', []):
                        book = _resolve(
                            Book,
                            slug,
                            'active book',
                            name,
                            self.stdout,
                            self.style,
                        )
                        if book is not None:
                            books.append(book)
                    faction.books_active_in.set(books)

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
                f'Factions seeded: {created_count} created, '
                f'{updated_count} updated, {error_count} errors.'
            )
        )
