import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.narrative.models import Prophecy, ProphecySubject


class SeedPropheciesCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for command in (
            'seed_books',
            'seed_gods',
            'seed_titans',
            'seed_characters',
            'seed_monsters',
        ):
            call_command(command, stdout=StringIO())

        cls.output = StringIO()
        call_command('seed_prophecies', stdout=cls.output)

    def test_seed_creates_prophecies_and_resolves_typed_subjects(self):
        self.assertEqual(Prophecy.objects.count(), 11)
        self.assertEqual(Prophecy.objects.filter(wiki_url__isnull=False).count(), 6)
        self.assertEqual(
            Prophecy.objects.get(slug='the-great-prophecy').wiki_url,
            'https://riordan.fandom.com/wiki/Great_Prophecy',
        )
        self.assertEqual(ProphecySubject.objects.count(), 39)
        self.assertNotIn('[WARN]', self.output.getvalue())

        lightning = Prophecy.objects.get(slug='the-lightning-thief-prophecy')
        self.assertTrue(lightning.subject_records.filter(subject_god__slug='ares').exists())
        titan_curse = Prophecy.objects.get(slug='the-titans-curse-prophecy')
        self.assertTrue(titan_curse.subject_records.filter(subject_titan__slug='atlas').exists())

        seven = Prophecy.objects.get(slug='the-prophecy-of-the-seven')
        self.assertIsNone(seven.fulfilled_in)
        self.assertEqual(seven.subject_records.filter(subject_character__isnull=False).count(), 7)
        for slug in ('jason-grace', 'piper-mclean', 'leo-valdez', 'frank-zhang', 'hazel-levesque'):
            self.assertTrue(seven.subject_records.filter(subject_character__slug=slug).exists())

    def test_sword_of_hades_links_story_and_parent_collection(self):
        prophecy = Prophecy.objects.get(slug='the-prophecy-of-the-sword-of-hades')
        self.assertEqual(prophecy.fulfilled_in.slug, 'percy-jackson-and-the-sword-of-hades')
        self.assertEqual(
            set(prophecy.books_relevant_to.values_list('slug', flat=True)),
            {'the-demigod-files', 'percy-jackson-and-the-sword-of-hades'},
        )

    def test_null_wiki_url_does_not_clear_existing_prophecy_url(self):
        prophecy = Prophecy.objects.get(slug='the-prophecy-of-the-sword-of-hades')
        prophecy.wiki_url = 'https://riordan.fandom.com/wiki/Existing_Prophecy'
        prophecy.save(update_fields=['wiki_url'])

        call_command('seed_prophecies', stdout=StringIO())

        prophecy.refresh_from_db()
        self.assertEqual(prophecy.wiki_url, 'https://riordan.fandom.com/wiki/Existing_Prophecy')

    def test_seed_command_is_idempotent(self):
        call_command('seed_prophecies', stdout=StringIO())
        self.assertEqual(Prophecy.objects.count(), 11)
        self.assertEqual(ProphecySubject.objects.count(), 39)

    def test_unresolved_references_warn_and_are_skipped(self):
        entry = {
            'title': 'Unresolved Prophecy',
            'expected_slug': 'unresolved-prophecy',
            'text': 'A test line.',
            'oracle_type': 'Oracle of Delphi',
            'delivered_by_slug': 'missing-character',
            'fulfilled_in_book_slug': 'missing-book',
            'subjects': [{'type': 'god', 'slug': 'missing-god'}],
            'books_relevant_to_slugs': ['missing-relevant-book'],
        }
        with TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / 'prophecies.json'
            data_file.write_text(json.dumps([entry]), encoding='utf-8')
            output = StringIO()
            with patch('apps.narrative.management.commands.seed_prophecies.DATA_FILE', data_file):
                call_command('seed_prophecies', stdout=output)

        prophecy = Prophecy.objects.get(slug='unresolved-prophecy')
        self.assertIsNone(prophecy.delivered_by)
        self.assertIsNone(prophecy.fulfilled_in)
        self.assertEqual(prophecy.subject_records.count(), 0)
        self.assertEqual(prophecy.books_relevant_to.count(), 0)
        self.assertEqual(output.getvalue().count('[WARN]'), 4)
