from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.narrative.models import Book


class SeedBooksCommandTests(TestCase):
    def test_seed_creates_canonical_books_and_collection_links(self):
        call_command('seed_books', stdout=StringIO())

        self.assertEqual(Book.objects.count(), 12)
        collection = Book.objects.get(slug='the-demigod-files')
        self.assertEqual(collection.book_type, 'short_story_collection')
        self.assertEqual(collection.included_stories.count(), 3)

        sword = Book.objects.get(slug='percy-jackson-and-the-sword-of-hades')
        self.assertEqual(sword.parent_collection, collection)
        self.assertIn('Persephone', sword.synopsis)
        self.assertEqual(
            Book.objects.get(title="The Titan's Curse").slug,
            'the-titans-curse',
        )

    def test_seed_is_idempotent(self):
        call_command('seed_books', stdout=StringIO())
        call_command('seed_books', stdout=StringIO())

        self.assertEqual(Book.objects.count(), 12)
        self.assertEqual(
            Book.objects.filter(parent_collection__slug='the-demigod-files').count(),
            3,
        )
