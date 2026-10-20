import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.divinities.models import DivineRelationship, God, Titan
from apps.narrative.models import Book
from tests.makers import make_book, make_god


class DivinitySeedCommandTests(TestCase):
    def test_seed_commands_populate_records_and_are_idempotent(self):
        outputs = []
        for command in (
            'seed_books',
            'seed_gods',
            'seed_titans',
            'seed_divine_relationships',
        ):
            output = StringIO()
            call_command(command, stdout=output)
            outputs.append(output.getvalue())

        self.assertEqual(Book.objects.count(), 12)
        self.assertEqual(God.objects.count(), 33)
        self.assertEqual(Titan.objects.count(), 9)
        self.assertEqual(DivineRelationship.objects.count(), 32)
        self.assertFalse(any('Warning:' in output for output in outputs))

        rerun_relationships = StringIO()
        call_command('seed_divine_relationships', stdout=rerun_relationships)

        self.assertEqual(DivineRelationship.objects.count(), 32)
        self.assertIn('Exists:', rerun_relationships.getvalue())

    def test_seeded_rhea_relationships_are_typed_as_titan(self):
        for command in (
            'seed_books',
            'seed_gods',
            'seed_titans',
            'seed_divine_relationships',
        ):
            call_command(command, stdout=StringIO())

        rhea = Titan.objects.get(slug='rhea')
        self.assertEqual(
            rhea.relationships_as_from.filter(relationship_type='parent_of').count(),
            6,
        )
        self.assertTrue(rhea.relationships_as_from.filter(relationship_type='child_of').exists())


class MissingBookSlugWarningTests(TestCase):
    def test_missing_book_slugs_warn_and_skip_only_missing_references(self):
        valid_book = make_book(title='Valid Book', book_number=1)
        god = make_god(name='Zeus', first_appearance_book=valid_book)
        data = [
            {
                'name': 'Zeus',
                'first_appearance_book_slug': 'missing-book',
                'books_appeared_in_slugs': ['valid-book', 'missing-book'],
            }
        ]

        with TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / 'gods.json'
            data_file.write_text(json.dumps(data), encoding='utf-8')
            output = StringIO()
            with patch('apps.divinities.management.commands.seed_gods.DATA_FILE', data_file):
                call_command('seed_gods', stdout=output)

        god.refresh_from_db()
        self.assertEqual(god.first_appearance_book, valid_book)
        self.assertEqual(list(god.books_appeared_in.all()), [valid_book])
        self.assertEqual(output.getvalue().count('Warning:'), 2)
        self.assertIn('Gods seeded: 0 created, 1 updated, 0 errors.', output.getvalue())
