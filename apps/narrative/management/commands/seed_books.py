"""
Management command: seed_books
Loads all V1 Book records from data/books.json.

Re-run safe: uses update_or_create on (series, book_number) so re-runs
update existing records rather than creating duplicates.

Note: narrator, main_characters, and antagonists are FK/M2M fields that
reference characters.Character. These are populated separately by
seed_characters once characters exist, to respect the dependency order.
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.narrative.models import Book

DATA_FILE = settings.BASE_DIR / "data" / "books.json"


class Command(BaseCommand):
    help = "Seed V1 Book records from data/books.json"

    def handle(self, *args, **kwargs):
        if not DATA_FILE.exists():
            self.stdout.write(self.style.ERROR(f"Data file not found: {DATA_FILE}"))
            return

        with open(DATA_FILE, "r") as f:
            books = json.load(f)

        created_count = 0
        updated_count = 0
        error_count = 0

        for entry in books:
            try:
                _, created = Book.objects.update_or_create(
                    series=entry["series"],
                    book_number=entry["book_number"],
                    defaults={
                        "title": entry["title"],
                        "published_date": entry.get("published_date"),
                        "synopsis": entry.get("synopsis"),
                        "short_description": entry.get("short_description"),
                        "book_type": entry.get("book_type", "novel"),
                        "camp_bead_description": entry.get("camp_bead_description"),
                        # narrator, main_characters, antagonists populated by seed_characters
                    },
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  Created: {entry['title']}")
                    )
                else:
                    updated_count += 1
                    self.stdout.write(f"  Updated: {entry['title']}")

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"  Failed:  {entry.get('title', 'unknown')} — {e}")
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Books seeded: {created_count} created, "
                f"{updated_count} updated, "
                f"{error_count} errors."
            )
        )
