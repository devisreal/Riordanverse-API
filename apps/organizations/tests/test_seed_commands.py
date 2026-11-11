import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.organizations.models import Cabin, Faction, FactionMember


class SeedOrganizationsCommandTests(TestCase):
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

        cls.cabin_output = StringIO()
        call_command('seed_cabins', stdout=cls.cabin_output)
        cls.faction_output = StringIO()
        call_command('seed_factions', stdout=cls.faction_output)

    def test_seed_cabins_resolves_references_and_canonical_slugs(self):
        self.assertEqual(Cabin.objects.count(), 20)
        self.assertEqual(Cabin.objects.filter(wiki_url__isnull=False).count(), 20)
        self.assertEqual(
            Cabin.objects.get(number=1).wiki_url,
            'https://riordan.fandom.com/wiki/Zeus%27s_Cabin',
        )
        self.assertNotIn('[WARN]', self.cabin_output.getvalue())
        self.assertTrue(Cabin.objects.filter(slug='cabin-2-hera', number=2).exists())
        self.assertTrue(Cabin.objects.filter(slug='cabin-8-artemis', number=8).exists())

        cabin_eight = Cabin.objects.get(number=8)
        self.assertIn(
            'phoebe-hunter',
            cabin_eight.known_campers.values_list('slug', flat=True),
        )
        self.assertEqual(cabin_eight.head_counselor.slug, 'zoe-nightshade')

    def test_seed_factions_resolves_all_typed_members(self):
        self.assertEqual(Faction.objects.count(), 8)
        self.assertEqual(Faction.objects.filter(wiki_url__isnull=False).count(), 5)
        self.assertEqual(
            Faction.objects.get(slug='titan-army').wiki_url,
            'https://riordan.fandom.com/wiki/Titan_Army',
        )
        self.assertEqual(FactionMember.objects.count(), 58)
        self.assertNotIn('[WARN]', self.faction_output.getvalue())

        council = Faction.objects.get(slug='olympian-council')
        self.assertEqual(council.member_records.filter(member_god__isnull=False).count(), 12)
        titan_army = Faction.objects.get(slug='titan-army')
        self.assertEqual(titan_army.member_records.filter(member_titan__isnull=False).count(), 7)
        self.assertEqual(titan_army.member_records.filter(member_monster__isnull=False).count(), 3)

        hunters = Faction.objects.get(slug='hunters-of-artemis')
        self.assertTrue(
            hunters.member_records.filter(member_character__slug='phoebe-hunter').exists()
        )
        cloven_elders = Faction.objects.get(slug='council-of-cloven-elders')
        self.assertTrue(
            cloven_elders.member_records.filter(member_character__slug='maron').exists()
        )

    def test_null_wiki_url_does_not_clear_existing_faction_url(self):
        faction = Faction.objects.get(slug='olympian-council')
        faction.wiki_url = 'https://riordan.fandom.com/wiki/Existing_Faction'
        faction.save(update_fields=['wiki_url'])

        call_command('seed_factions', stdout=StringIO())

        faction.refresh_from_db()
        self.assertEqual(faction.wiki_url, 'https://riordan.fandom.com/wiki/Existing_Faction')

    def test_null_wiki_url_does_not_clear_existing_cabin_url(self):
        cabin = Cabin.objects.create(number=21, is_honorary=False, is_empty=False)
        cabin.wiki_url = 'https://riordan.fandom.com/wiki/Existing_Cabin'
        cabin.save(update_fields=['wiki_url'])
        entry = {
            'number': 21,
            'expected_slug': cabin.slug,
            'is_honorary': False,
            'is_empty': False,
            'wiki_url': None,
        }

        with TemporaryDirectory() as directory:
            data_file = Path(directory) / 'cabins.json'
            data_file.write_text(json.dumps([entry]), encoding='utf-8')
            with patch('apps.organizations.management.commands.seed_cabins.DATA_FILE', data_file):
                call_command('seed_cabins', stdout=StringIO())

        cabin.refresh_from_db()
        self.assertEqual(cabin.wiki_url, 'https://riordan.fandom.com/wiki/Existing_Cabin')

    def test_seed_commands_are_idempotent(self):
        call_command('seed_cabins', stdout=StringIO())
        call_command('seed_factions', stdout=StringIO())
        self.assertEqual(Cabin.objects.count(), 20)
        self.assertEqual(Faction.objects.count(), 8)
        self.assertEqual(FactionMember.objects.count(), 58)
