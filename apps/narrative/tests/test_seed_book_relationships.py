import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.narrative.models import BookMainCharacter
from tests.makers import (
    make_book,
    make_character,
    make_creature,
    make_god,
    make_monster,
    make_titan,
)


class SeedBookRelationshipsCommandTests(TestCase):
    def setUp(self):
        self.book = make_book(title='The Lightning Thief', book_number=1)
        self.percy = make_character(name='Percy Jackson')
        self.apollo = make_god(name='Apollo')
        self.kronos = make_titan(name='Kronos')
        self.medusa = make_monster(name='Medusa')
        self.myrmekes = make_creature(name='Myrmekes')
        self.entries = [
            {
                'book_slug': self.book.slug,
                'narrator_slug': self.percy.slug,
                'main_characters': [
                    {'type': 'character', 'slug': self.percy.slug},
                    {'type': 'god', 'slug': self.apollo.slug},
                    {'type': 'titan', 'slug': self.kronos.slug},
                    {'type': 'monster', 'slug': self.medusa.slug},
                    {'type': 'creature', 'slug': self.myrmekes.slug},
                ],
                'antagonists': [
                    {'type': 'character', 'slug': self.percy.slug},
                    {'type': 'god', 'slug': self.apollo.slug},
                    {'type': 'titan', 'slug': self.kronos.slug},
                    {'type': 'monster', 'slug': self.medusa.slug},
                    {'type': 'creature', 'slug': self.myrmekes.slug},
                ],
            }
        ]

    def _run_with_entries(self, entries, stdout):
        with tempfile.TemporaryDirectory() as directory:
            data_file = Path(directory) / 'book_relationships.json'
            data_file.write_text(json.dumps(entries), encoding='utf-8')
            with patch(
                'apps.narrative.management.commands.seed_book_relationships.DATA_FILE', data_file
            ):
                call_command('seed_book_relationships', stdout=stdout)

    def test_seeds_all_supported_types_and_keeps_character_m2m_compatibility(self):
        from io import StringIO

        output = StringIO()
        self._run_with_entries(self.entries, output)

        self.book.refresh_from_db()
        self.assertEqual(self.book.narrator, self.percy)
        self.assertEqual(self.book.narrator_records.count(), 1)
        self.assertEqual(list(self.book.narrators.all()), [self.percy])
        self.assertEqual(self.book.main_character_records.count(), 5)
        self.assertEqual(self.book.antagonist_records.count(), 5)
        self.assertEqual(list(self.book.main_characters.all()), [self.percy])
        self.assertEqual(list(self.book.antagonists.all()), [self.percy])
        self.assertIn('5 main-character links', output.getvalue())

    def test_seed_accepts_legacy_character_narrator_slug_list(self):
        from io import StringIO

        entry = {
            'book_slug': self.book.slug,
            'narrator_slugs': [self.percy.slug],
            'main_characters': [],
            'antagonists': [],
        }
        self._run_with_entries([entry], StringIO())

        self.book.refresh_from_db()
        self.assertEqual(self.book.narrator, self.percy)
        self.assertEqual(self.book.narrator_records.count(), 1)

    def test_seed_supports_all_typed_narrator_entity_types(self):
        from io import StringIO

        entry = {
            'book_slug': self.book.slug,
            'narrator_slugs': [self.percy.slug],
            'narrators': [
                {'type': 'character', 'slug': self.percy.slug, 'name': self.percy.name},
                {'type': 'god', 'slug': self.apollo.slug, 'name': self.apollo.name},
                {'type': 'titan', 'slug': self.kronos.slug, 'name': self.kronos.name},
                {'type': 'monster', 'slug': self.medusa.slug, 'name': self.medusa.name},
                {'type': 'creature', 'slug': self.myrmekes.slug, 'name': self.myrmekes.name},
            ],
            'main_characters': [],
            'antagonists': [],
        }
        self._run_with_entries([entry], StringIO())

        self.book.refresh_from_db()
        self.assertEqual(self.book.narrator_records.count(), 5)
        self.assertIsNone(self.book.narrator)
        self.assertEqual(list(self.book.narrators.all()), [self.percy])

    def test_seed_is_idempotent_and_replaces_obsolete_typed_links(self):
        from io import StringIO

        BookMainCharacter.objects.create(book=self.book, character=self.percy)
        first_output = StringIO()
        self._run_with_entries(self.entries, first_output)
        second_output = StringIO()
        self._run_with_entries(self.entries, second_output)

        self.assertEqual(self.book.main_character_records.count(), 5)
        self.assertEqual(self.book.antagonist_records.count(), 5)
        self.assertIn('0 links created', second_output.getvalue())

    def test_missing_references_warn_and_are_skipped_or_set_null(self):
        from io import StringIO

        entry = {
            'book_slug': self.book.slug,
            'narrator_slug': 'not-seeded',
            'main_characters': [{'type': 'monster', 'slug': 'not-seeded'}],
            'antagonists': [],
        }
        output = StringIO()
        self._run_with_entries([entry], output)

        self.book.refresh_from_db()
        self.assertIsNone(self.book.narrator)
        self.assertEqual(self.book.main_character_records.count(), 0)
        self.assertIn('Unresolved character narrator', output.getvalue())
        self.assertIn('Unresolved monster main character', output.getvalue())

    def test_canonical_file_has_child_story_links_and_myrmekes_creature(self):
        from apps.narrative.management.commands.seed_book_relationships import DATA_FILE

        with DATA_FILE.open(encoding='utf-8') as data_file:
            entries = json.load(data_file)

        by_book = {entry['book_slug']: entry for entry in entries}
        self.assertEqual(len(entries), 12)
        for entry in entries:
            self.assertEqual(entry['narrator_slugs'], ['percy-jackson'])
            self.assertEqual(
                entry['narrators'],
                [
                    {
                        'type': 'character',
                        'slug': 'percy-jackson',
                        'name': 'Percy Jackson',
                    }
                ],
            )
            self.assertNotIn('narrator_slug', entry)

        entity_files = {
            'character': 'characters.json',
            'god': 'gods.json',
            'titan': 'titans.json',
            'monster': 'monsters.json',
            'creature': 'creatures.json',
        }
        for entry in entries:
            character_slugs = []
            for narrator in entry['narrators']:
                records = json.loads(
                    (DATA_FILE.parent / entity_files[narrator['type']]).read_text(encoding='utf-8')
                )
                match = next(
                    record
                    for record in records
                    if record.get('expected_slug', record.get('slug')) == narrator['slug']
                )
                self.assertEqual(narrator['name'], match['name'])
                if narrator['type'] == 'character':
                    character_slugs.append(narrator['slug'])
            self.assertEqual(entry['narrator_slugs'], character_slugs)

        collection = by_book['the-demigod-files']
        self.assertEqual(collection['main_characters'], [])
        self.assertEqual(collection['antagonists'], [])

        bronze_dragon = by_book['percy-jackson-and-the-bronze-dragon']
        self.assertIn(
            {'type': 'creature', 'slug': 'myrmekes'},
            bronze_dragon['antagonists'],
        )
        stolen_chariot = by_book['percy-jackson-and-the-stolen-chariot']
        self.assertEqual(
            stolen_chariot['main_characters'],
            [
                {'type': 'character', 'slug': 'percy-jackson'},
                {'type': 'character', 'slug': 'clarisse-la-rue'},
            ],
        )
