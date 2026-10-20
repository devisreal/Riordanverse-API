"""Seed Prophecy records and typed subjects from ``data/prophecies.json``.

Books, Gods, Titans, Characters, and Monsters should be seeded first. Missing
foreign-key and subject references warn and are skipped or left null.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from apps.bestiary.models import Monster
from apps.characters.models import Character
from apps.divinities.models import God, Titan
from apps.narrative.models import Book, Prophecy, ProphecySubject

DATA_FILE = settings.BASE_DIR / 'data' / 'prophecies.json'

ENTITY_MODELS = {
    'character': Character,
    'god': God,
    'titan': Titan,
    'monster': Monster,
}


def _resolve(model, slug, relation, prophecy_title, stdout, style):
    if not slug:
        return None
    try:
        return model.objects.get(slug=slug)
    except model.DoesNotExist:
        stdout.write(
            style.WARNING(
                f"[WARN] Unresolved {relation} '{slug}' for {prophecy_title} — skipping reference."
            )
        )
        return None


class Command(BaseCommand):
    help = 'Seed prophecies from data/prophecies.json.'

    def handle(self, *args, **kwargs):
        if not DATA_FILE.exists():
            raise CommandError(f'Prophecy data file not found: {DATA_FILE}')

        with DATA_FILE.open(encoding='utf-8') as data_file:
            entries = json.load(data_file)

        if not isinstance(entries, list):
            raise CommandError('Prophecy data must be a JSON list.')

        created_count = 0
        updated_count = 0
        error_count = 0

        for entry in entries:
            title = entry.get('title', 'unknown')
            try:
                with transaction.atomic():
                    prophecy, created = Prophecy.objects.update_or_create(
                        slug=entry['expected_slug'],
                        defaults={
                            'title': title,
                            'text': entry['text'],
                            'oracle_type': entry.get('oracle_type'),
                            'delivered_by': _resolve(
                                Character,
                                entry.get('delivered_by_slug'),
                                'deliverer',
                                title,
                                self.stdout,
                                self.style,
                            ),
                            'fulfilled_in': _resolve(
                                Book,
                                entry.get('fulfilled_in_book_slug'),
                                'fulfillment book',
                                title,
                                self.stdout,
                                self.style,
                            ),
                            'interpretation_notes': entry.get('interpretation_notes'),
                            'description': entry.get('description'),
                        },
                    )

                    desired_subjects = {}
                    for subject_ref in entry.get('subjects', []):
                        subject_type = subject_ref.get('type')
                        model = ENTITY_MODELS.get(subject_type)
                        if model is None:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"[WARN] Unknown subject type '{subject_type}' for {title} — skipping."
                                )
                            )
                            continue

                        slug = subject_ref.get('slug')
                        entity = _resolve(
                            model,
                            slug,
                            f'{subject_type} subject',
                            title,
                            self.stdout,
                            self.style,
                        )
                        if entity is not None:
                            desired_subjects[(subject_type, entity.pk)] = entity

                    current_subjects = list(
                        prophecy.subject_records.select_related(
                            'subject_character',
                            'subject_god',
                            'subject_titan',
                            'subject_monster',
                        )
                    )
                    for subject_link in current_subjects:
                        existing_type = next(
                            (
                                subject_type
                                for subject_type in ENTITY_MODELS
                                if getattr(subject_link, f'subject_{subject_type}_id') is not None
                            ),
                            None,
                        )
                        if existing_type is None:
                            subject_link.delete()
                            continue
                        existing_subject = getattr(subject_link, f'subject_{existing_type}')
                        if (existing_type, existing_subject.pk) not in desired_subjects:
                            subject_link.delete()

                    for (subject_type, _), entity in desired_subjects.items():
                        ProphecySubject.objects.get_or_create(
                            prophecy=prophecy,
                            **{f'subject_{subject_type}': entity},
                        )

                    books = []
                    for slug in entry.get('books_relevant_to_slugs', []):
                        book = _resolve(
                            Book,
                            slug,
                            'relevant book',
                            title,
                            self.stdout,
                            self.style,
                        )
                        if book is not None:
                            books.append(book)
                    prophecy.books_relevant_to.set(books)

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
                f'Prophecies seeded: {created_count} created, '
                f'{updated_count} updated, {error_count} errors.'
            )
        )
