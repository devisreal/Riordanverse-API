import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.characters.models import Character, Power
from apps.divinities.family import serialize_family
from tests.makers import make_character, make_divine_relationship, make_god


class PowerSeedCommandTests(TestCase):
    def test_seed_powers_resolves_relations_and_is_idempotent(self):
        outputs = []
        for command in (
            'seed_books',
            'seed_gods',
            'seed_titans',
            'seed_characters',
            'seed_items',
            'seed_monsters',
            'seed_creatures',
            'seed_divine_relationships',
            'seed_powers',
        ):
            output = StringIO()
            call_command(command, stdout=output)
            outputs.append(output.getvalue())

        self.assertEqual(Power.objects.count(), 14)
        self.assertEqual(Power.objects.filter(wiki_url__isnull=False).count(), 8)
        self.assertFalse(any('[WARN]' in output for output in outputs), '\n'.join(outputs))

        percy = Character.objects.get(slug='percy-jackson')
        hydrokinesis = percy.powers.get(name='Hydrokinesis')
        self.assertEqual(hydrokinesis.type, 'offensive')
        self.assertEqual(hydrokinesis.source, 'divine_parent')
        self.assertEqual(hydrokinesis.first_demonstrated_book.slug, 'the-lightning-thief')
        self.assertEqual(hydrokinesis.display_order, 0)
        self.assertEqual(hydrokinesis.wiki_url, 'https://riordan.fandom.com/wiki/Hydrokinesis')
        self.assertIsNone(percy.powers.get(name='Personal Hurricane').wiki_url)

        celedon = Character.objects.get(slug='celedon')
        vocal_enchantment = celedon.powers.get(name='Hypnotic Vocal Enchantment')
        self.assertEqual(vocal_enchantment.source, 'creation')
        self.assertEqual(
            vocal_enchantment.first_demonstrated_book.slug, 'percy-jackson-and-the-singer-of-apollo'
        )

        rerun = StringIO()
        call_command('seed_powers', stdout=rerun)
        self.assertEqual(Power.objects.count(), 14)
        self.assertIn('14 updated', rerun.getvalue())

    def test_null_wiki_url_does_not_clear_existing_power_url(self):
        percy = make_character(name='Percy Jackson')
        power = Power.objects.create(
            character=percy,
            name='Personal Hurricane',
            wiki_url='https://riordan.fandom.com/wiki/Existing_Hurricane',
        )
        data = [
            {
                'character_slug': percy.slug,
                'name': 'Personal Hurricane',
                'wiki_url': None,
            }
        ]

        with TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / 'powers.json'
            data_file.write_text(json.dumps(data), encoding='utf-8')
            with patch('apps.characters.management.commands.seed_powers.DATA_FILE', data_file):
                call_command('seed_powers', stdout=StringIO())

        power.refresh_from_db()
        self.assertEqual(power.wiki_url, 'https://riordan.fandom.com/wiki/Existing_Hurricane')

    def test_divine_parent_mismatch_warns_without_duplicating_parent(self):
        poseidon = make_god(name='Poseidon')
        percy = make_character(name='Percy Jackson')
        make_divine_relationship(from_entity=poseidon, to_entity=percy)
        data = [
            {
                'character_slug': percy.slug,
                'name': 'Test Power',
                'power_type': 'offensive',
                'source': 'divine_parent',
                'divine_parent_slug': 'zeus',
                'description': 'A test ability.',
                'scope': [],
                'is_passive': False,
                'first_demonstrated_book': None,
            }
        ]

        with TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / 'powers.json'
            data_file.write_text(json.dumps(data), encoding='utf-8')
            output = StringIO()
            with patch('apps.characters.management.commands.seed_powers.DATA_FILE', data_file):
                call_command('seed_powers', stdout=output)

        self.assertEqual(Power.objects.count(), 1)
        self.assertIn('Divine-parent check failed', output.getvalue())
        self.assertEqual(serialize_family(percy)['parents'][0]['slug'], 'poseidon')
