from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.bestiary.models import Monster, MonsterDefeat


class MonsterSeedCommandTests(TestCase):
    def test_seed_resolves_relations_and_is_idempotent(self):
        for command in (
            'seed_books',
            'seed_gods',
            'seed_titans',
            'seed_characters',
        ):
            call_command(command, stdout=StringIO())

        output = StringIO()
        call_command('seed_monsters', stdout=output)

        self.assertEqual(Monster.objects.count(), 29)
        self.assertEqual(Monster.objects.filter(wiki_url__isnull=False).count(), 29)
        self.assertEqual(Monster.objects.get(slug='minotaur').name, 'The Minotaur')
        self.assertEqual(
            Monster.objects.get(slug='alecto').wiki_url,
            'https://riordan.fandom.com/wiki/Alecto',
        )
        antaeus = Monster.objects.get(slug='antaeus')
        self.assertEqual(antaeus.monster_type, 'giant')
        self.assertEqual(antaeus.wiki_url, 'https://riordan.fandom.com/wiki/Antaeus')
        self.assertEqual(antaeus.first_appearance_book.slug, 'the-battle-of-the-labyrinth')
        self.assertEqual(MonsterDefeat.objects.count(), 0)
        self.assertEqual(
            Monster.objects.get(slug='polyphemus').defeated_by.count(),
            0,
        )
        self.assertIn(
            'percy-jacksons-greek-heroes',
            Monster.objects.get(slug='medusa').books_appeared_in.values_list('slug', flat=True),
        )

        defeat_output = StringIO()
        call_command('seed_monster_defeats', stdout=defeat_output)
        self.assertEqual(MonsterDefeat.objects.count(), 27)
        self.assertNotIn("Unresolved Character 'odysseus'", defeat_output.getvalue())
        self.assertTrue(
            MonsterDefeat.objects.filter(
                monster__slug='polyphemus',
                defeated_by__slug='odysseus',
                is_myth=True,
            ).exists()
        )
        self.assertTrue(
            MonsterDefeat.objects.filter(
                monster__slug='polyphemus',
                defeated_by__slug='percy-jackson',
                book__slug='the-sea-of-monsters',
                is_myth=False,
            ).exists()
        )
        cerberus_heracles = MonsterDefeat.objects.get(
            monster__slug='cerberus', defeated_by__slug='heracles'
        )
        self.assertIsNone(cerberus_heracles.book)
        self.assertTrue(cerberus_heracles.is_myth)

        defeat_rerun = StringIO()
        call_command('seed_monster_defeats', stdout=defeat_rerun)
        self.assertEqual(MonsterDefeat.objects.count(), 27)
        self.assertIn('27 existing', defeat_rerun.getvalue())

        rerun = StringIO()
        call_command('seed_monsters', stdout=rerun)
        self.assertEqual(Monster.objects.count(), 29)
        self.assertIn('29 updated', rerun.getvalue())
