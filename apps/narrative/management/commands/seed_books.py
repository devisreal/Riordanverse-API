"""Idempotently seed canonical Book records and their collection hierarchy."""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Max

from apps.narrative.models import Book

DATA_FILE = settings.BASE_DIR / 'data' / 'books.json'


class Command(BaseCommand):
    help = 'Seed canonical Book records from data/books.json'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        if not DATA_FILE.exists():
            raise CommandError(f'Book data file not found: {DATA_FILE}')

        with DATA_FILE.open(encoding='utf-8') as data_file:
            entries = json.load(data_file)

        if not isinstance(entries, list):
            raise CommandError('Book data must be a JSON list.')

        expected_slugs = [entry.get('expected_slug') for entry in entries]
        if any(not slug for slug in expected_slugs):
            raise CommandError('Every book record must have an expected_slug.')
        if len(expected_slugs) != len(set(expected_slugs)):
            raise CommandError('Book data contains duplicate expected_slug values.')

        # Move existing records out of the way first. This allows a re-seed to
        # safely reorder companion titles without violating the unique
        # (series, book_number) constraint during the update.
        existing = list(Book.objects.filter(slug__in=expected_slugs).order_by('pk'))
        highest_number = Book.objects.aggregate(highest=Max('book_number'))['highest'] or 0
        staging_number = highest_number + len(existing) + len(entries) + 1
        for index, book in enumerate(existing):
            book.book_number = staging_number + index
            book.save(update_fields=['book_number'])

        books_by_slug = {}
        created_count = 0
        updated_count = 0
        for index, entry in enumerate(entries):
            slug = entry['expected_slug']
            temporary_number = staging_number + len(existing) + index
            defaults = {
                'title': entry['title'],
                'series': entry['series'],
                'book_number': temporary_number,
                'published_date': entry.get('published_date'),
                'synopsis': entry.get('synopsis'),
                'short_description': entry.get('short_description'),
                'book_type': entry.get('book_type', 'novel'),
                'camp_bead_description': entry.get('camp_bead_description'),
                'parent_collection': None,
            }
            if entry.get('wiki_url'):
                defaults['wiki_url'] = entry['wiki_url']

            book, created = Book.objects.update_or_create(slug=slug, defaults=defaults)
            if book.slug != slug:
                raise CommandError(
                    f'Book slug mismatch for {entry["title"]!r}: '
                    f'expected {slug!r}, generated {book.slug!r}.'
                )
            books_by_slug[slug] = book
            if created:
                created_count += 1
            else:
                updated_count += 1

        # Resolve references only after every row has been created/updated.
        for entry in entries:
            book = books_by_slug[entry['expected_slug']]
            parent_slug = entry.get('parent_collection_slug')
            if parent_slug and parent_slug not in books_by_slug:
                raise CommandError(
                    f'Unknown parent_collection_slug {parent_slug!r} '
                    f'for book {entry["expected_slug"]!r}.'
                )
            parent = books_by_slug.get(parent_slug) if parent_slug else None
            if book.parent_collection_id != (parent.pk if parent else None):
                book.parent_collection = parent
                book.save(update_fields=['parent_collection'])

        # Ensure that no non-seed record occupies a canonical ordering slot.
        seeded_ids = [book.pk for book in books_by_slug.values()]
        for entry in entries:
            conflict = Book.objects.filter(
                series=entry['series'], book_number=entry['book_number']
            ).exclude(pk__in=seeded_ids)
            if conflict.exists():
                raise CommandError(
                    f'Cannot assign {entry["series"]} book number {entry["book_number"]}: '
                    'it is already used by a non-seed Book record.'
                )

        # Restore the canonical order after all target slots are free.
        for entry in entries:
            book = books_by_slug[entry['expected_slug']]
            book.series = entry['series']
            book.book_number = entry['book_number']
            book.save(update_fields=['series', 'book_number'])

        self.stdout.write(
            self.style.SUCCESS(
                f'Books seeded: {created_count} created, {updated_count} updated, '
                f'{len(books_by_slug)} linked/verified.'
            )
        )
