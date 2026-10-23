import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.narrative.models import Quest, QuestCasualty, QuestParticipant


class SeedQuestsCommandTests(TestCase):
    seed_commands = (
        'seed_books',
        'seed_gods',
        'seed_titans',
        'seed_characters',
        'seed_monsters',
        'seed_items',
        'seed_locations',
        'seed_prophecies',
        'seed_quests',
    )

    def seed_all(self):
        outputs = []
        for command in self.seed_commands:
            output = StringIO()
            call_command(command, stdout=output)
            outputs.append(output.getvalue())
        return outputs

    def test_seed_resolves_typed_links_and_is_idempotent(self):
        outputs = self.seed_all()

        self.assertEqual(Quest.objects.count(), 12)
        self.assertEqual(Quest.objects.filter(wiki_url__isnull=False).count(), 11)
        self.assertEqual(
            Quest.objects.get(slug='quest-for-zeuss-master-bolt').wiki_url,
            'https://riordan.fandom.com/wiki/Quest_for_the_Master_Bolt',
        )
        self.assertEqual(QuestParticipant.objects.count(), 34)
        self.assertEqual(QuestCasualty.objects.count(), 10)
        self.assertFalse(any('[WARN]' in output for output in outputs))

        child_story_books = {
            'quest-for-ares-stolen-chariot': 'percy-jackson-and-the-stolen-chariot',
            'quest-for-the-bronze-dragon': 'percy-jackson-and-the-bronze-dragon',
            'quest-for-the-sword-of-hades': 'percy-jackson-and-the-sword-of-hades',
            'quest-for-the-singer-of-apollo': 'percy-jackson-and-the-singer-of-apollo',
        }
        for quest_slug, book_slug in child_story_books.items():
            with self.subTest(quest=quest_slug):
                self.assertEqual(Quest.objects.get(slug=quest_slug).book.slug, book_slug)

        apollo_quest = Quest.objects.get(slug='quest-for-the-singer-of-apollo')
        apollo_link = apollo_quest.participant_records.get(participant_god__slug='apollo')
        self.assertEqual(apollo_link.participant_god.name, 'Apollo')

        minotaur_quest = Quest.objects.get(slug='quest-of-theseus')
        self.assertEqual(minotaur_quest.book.slug, 'percy-jacksons-greek-heroes')
        self.assertEqual(
            minotaur_quest.casualty_records.get().casualty_monster.slug,
            'minotaur',
        )

        chariot_quest = Quest.objects.get(slug='quest-for-ares-stolen-chariot')
        self.assertIn(
            'war-chariot',
            chariot_quest.items_recovered.values_list('slug', flat=True),
        )
        self.assertIn(
            'brooklyn-zoo',
            chariot_quest.locations_visited.values_list('slug', flat=True),
        )

        rerun = StringIO()
        call_command('seed_quests', stdout=rerun)
        self.assertEqual(Quest.objects.count(), 12)
        self.assertEqual(QuestParticipant.objects.count(), 34)
        self.assertEqual(QuestCasualty.objects.count(), 10)
        self.assertIn('12 updated', rerun.getvalue())

    def test_null_wiki_url_does_not_clear_existing_quest_url(self):
        self.seed_all()
        quest = Quest.objects.get(slug='quest-of-bellerophon')
        quest.wiki_url = 'https://riordan.fandom.com/wiki/Existing_Quest'
        quest.save(update_fields=['wiki_url'])

        call_command('seed_quests', stdout=StringIO())

        quest.refresh_from_db()
        self.assertEqual(quest.wiki_url, 'https://riordan.fandom.com/wiki/Existing_Quest')

    def test_unresolved_references_warn_and_are_skipped(self):
        entry = {
            'title': 'Partial Quest',
            'expected_slug': 'partial-quest',
            'book_slug': 'missing-book',
            'participants': [
                {'type': 'character', 'slug': 'missing-character'},
                {'type': 'unknown', 'slug': 'ignored'},
            ],
            'casualties': [{'type': 'monster', 'slug': 'missing-monster'}],
        }
        with TemporaryDirectory() as directory:
            data_file = Path(directory) / 'quests.json'
            data_file.write_text(json.dumps([entry]), encoding='utf-8')
            output = StringIO()
            with patch('apps.narrative.management.commands.seed_quests.DATA_FILE', data_file):
                call_command('seed_quests', stdout=output)

        quest = Quest.objects.get(slug='partial-quest')
        self.assertIsNone(quest.book)
        self.assertEqual(quest.participant_records.count(), 0)
        self.assertEqual(quest.casualty_records.count(), 0)
        self.assertIn("Unresolved book 'missing-book'", output.getvalue())
        self.assertIn("Unresolved participant character 'missing-character'", output.getvalue())
        self.assertIn("Unresolved casualty monster 'missing-monster'", output.getvalue())
        self.assertIn("Unknown participant entity type 'unknown'", output.getvalue())
        self.assertIn('0 errors', output.getvalue())
