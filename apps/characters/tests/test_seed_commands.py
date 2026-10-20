import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.characters.models import Character
from tests.makers import make_book


class SeedCharactersCommandTests(TestCase):
    def test_seed_v3_records_and_titan_parent(self):
        for command in ('seed_books', 'seed_gods', 'seed_titans'):
            call_command(command, stdout=StringIO())

        output = StringIO()
        call_command('seed_characters', stdout=output)

        phaethon = Character.objects.get(slug='phaethon')
        self.assertEqual(phaethon.divine_parent_titan.slug, 'helios')
        self.assertEqual(
            phaethon.special_states,
            ["Struck down by Zeus's lightning bolt to stop the sun chariot from burning the Earth"],
        )
        self.assertEqual(Character.objects.count(), 53)
        for slug in ('daedalus', 'eurytion', 'king-minos', 'perseus'):
            self.assertIsNone(Character.objects.get(slug=slug).cabin_number)
        self.assertNotIn('[WARN]', output.getvalue())

        rerun_output = StringIO()
        call_command('seed_characters', stdout=rerun_output)
        self.assertEqual(Character.objects.count(), 53)
        self.assertIn(
            'Characters seeded: 0 created, 53 updated, 0 errors.', rerun_output.getvalue()
        )

    def test_unresolved_foreign_keys_are_null_and_slug_lists_omit_missing_refs(self):
        valid_book = make_book(title='Valid Book')
        data = [
            {
                'name': 'Unresolved References Character',
                'expected_slug': 'unresolved-references-character',
                'character_type': 'mortal',
                'species': 'human',
                'divine_parent_slug': 'missing-divine-parent',
                'mortal_parent_ref_slug': 'missing-mortal-parent',
                'empathy_link_slug': 'missing-empathy-link',
                'first_appearance_book_slug': 'missing-first-book',
                'sibling_slugs': ['missing-sibling'],
                'books_appeared_in_slugs': [valid_book.slug, 'missing-appeared-book'],
            }
        ]

        with TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / 'characters.json'
            data_file.write_text(json.dumps(data), encoding='utf-8')
            output = StringIO()
            with patch('apps.characters.management.commands.seed_characters.DATA_FILE', data_file):
                call_command('seed_characters', stdout=output)

        character = Character.objects.get(slug='unresolved-references-character')
        self.assertIsNone(character.divine_parent)
        self.assertIsNone(character.divine_parent_titan)
        self.assertIsNone(character.mortal_parent_ref)
        self.assertIsNone(character.empathy_link)
        self.assertIsNone(character.first_appearance_book)
        self.assertEqual(list(character.siblings.all()), [])
        self.assertEqual(list(character.books_appeared_in.all()), [valid_book])
        self.assertEqual(output.getvalue().count('[WARN]'), 6)
        self.assertIn(
            "[WARN] Unresolved divine parent 'missing-divine-parent'",
            output.getvalue(),
        )
