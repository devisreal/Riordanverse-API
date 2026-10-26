import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.characters.models import Character
from apps.divinities.models import DivineRelationship, God, Titan
from apps.divinities.serializers import TitanDetailSerializer
from apps.items.models import Weapon
from apps.narrative.models import Book
from tests.makers import make_book, make_god, make_titan


class DivinitySeedCommandTests(TestCase):
    def test_seed_commands_populate_records_and_are_idempotent(self):
        outputs = []
        for command in (
            'seed_books',
            'seed_gods',
            'seed_titans',
            'seed_characters',
            'seed_items',
            'seed_divine_relationships',
        ):
            output = StringIO()
            call_command(command, stdout=output)
            outputs.append(output.getvalue())

        self.assertEqual(Book.objects.count(), 12)
        self.assertEqual(God.objects.count(), 37)
        self.assertEqual(God.objects.filter(wiki_url__isnull=False).count(), 37)
        self.assertEqual(
            God.objects.get(slug='tartarus').wiki_url,
            'https://riordan.fandom.com/wiki/Tartarus_(primordial)',
        )
        self.assertEqual(Titan.objects.count(), 19)
        self.assertEqual(Titan.objects.filter(wiki_url__isnull=False).count(), 17)
        self.assertEqual(Weapon.objects.count(), 50)
        self.assertEqual(
            Titan.objects.get(slug='kronos').wiki_url,
            'https://riordan.fandom.com/wiki/Kronos',
        )
        self.assertEqual(DivineRelationship.objects.count(), 138)
        self.assertEqual(Character.objects.count(), 68)
        helios = Titan.objects.get(slug='helios')
        tartarus = God.objects.get(slug='tartarus')
        amphitrite = God.objects.get(slug='amphitrite')
        poseidon = God.objects.get(slug='poseidon')
        kronos = Titan.objects.get(slug='kronos')
        gaea = God.objects.get(slug='gaea')
        phaethon = Character.objects.get(slug='phaethon')
        circe = God.objects.get(slug='circe')
        self.assertEqual(phaethon.divine_parent_titan, helios)
        self.assertEqual(helios.sacred_animals, ['rooster', 'white horses'])
        self.assertEqual(helios.sacred_plants, ['heliotrope'])
        self.assertEqual(Titan.objects.get(slug='rhea').sacred_animals, ['lion'])
        self.assertEqual(Titan.objects.get(slug='epimetheus').generation, 'younger_titan')
        self.assertEqual(Titan.objects.get(slug='epimetheus').alignment, 'kronos_army')
        self.assertEqual(Titan.objects.get(slug='eos').home, 'Sky / Palace of the Sun')
        self.assertSetEqual(
            set(God.objects.get(slug='zeus').children_demigods.values_list('slug', flat=True)),
            {'thalia-grace', 'perseus', 'heracles', 'tantalus', 'king-minos'},
        )
        self.assertSetEqual(
            set(God.objects.get(slug='zeus').weapons.values_list('slug', flat=True)),
            {'master-lightning-bolt', 'aegis'},
        )
        self.assertSetEqual(
            set(kronos.weapons.values_list('slug', flat=True)),
            {'kronos-scythe', 'adamantine-scythe', 'backbiter'},
        )
        atlas = Titan.objects.get(slug='atlas')
        self.assertIn(
            'epimetheus',
            [sibling['slug'] for sibling in TitanDetailSerializer(atlas).data['siblings']],
        )
        self.assertEqual(tartarus.tier, 'primordial')
        self.assertTrue(
            DivineRelationship.objects.filter(
                from_god=poseidon,
                to_god=amphitrite,
                relationship_type='consort_of',
            ).exists()
        )
        self.assertTrue(
            DivineRelationship.objects.filter(
                from_god=gaea,
                to_titan=kronos,
                relationship_type='parent_of',
            ).exists()
        )
        self.assertTrue(
            DivineRelationship.objects.filter(
                from_titan=helios,
                to_character=phaethon,
                relationship_type='parent_of',
            ).exists()
        )
        self.assertTrue(
            DivineRelationship.objects.filter(
                from_titan=helios,
                to_god=circe,
                relationship_type='parent_of',
            ).exists()
        )
        self.assertFalse(any('[WARN]' in output for output in outputs))

        rerun_relationships = StringIO()
        call_command('seed_divine_relationships', stdout=rerun_relationships)

        self.assertEqual(DivineRelationship.objects.count(), 138)
        self.assertIn('Exists:', rerun_relationships.getvalue())

    def test_seed_titan_preserves_existing_url_when_source_url_is_missing(self):
        titan = make_titan(
            name='Atlas',
            home='Existing home',
            wiki_url='https://riordan.fandom.com/wiki/Existing_Atlas',
        )
        data = [{'name': 'Atlas'}]

        with TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / 'titans.json'
            data_file.write_text(json.dumps(data), encoding='utf-8')
            with patch('apps.divinities.management.commands.seed_titans.DATA_FILE', data_file):
                call_command('seed_titans', stdout=StringIO())

        titan.refresh_from_db()
        self.assertEqual(titan.wiki_url, 'https://riordan.fandom.com/wiki/Existing_Atlas')
        self.assertEqual(titan.home, 'Existing home')

    def test_seeded_rhea_relationships_are_typed_as_titan(self):
        for command in (
            'seed_books',
            'seed_gods',
            'seed_titans',
            'seed_characters',
            'seed_items',
            'seed_divine_relationships',
        ):
            call_command(command, stdout=StringIO())

        rhea = Titan.objects.get(slug='rhea')
        self.assertEqual(
            rhea.relationships_as_from.filter(relationship_type='parent_of').count(),
            6,
        )
        self.assertTrue(rhea.relationships_as_from.filter(relationship_type='child_of').exists())


class MissingRelationshipEntityWarningTests(TestCase):
    def test_sibling_arrays_create_one_symmetric_relationship(self):
        atlas = make_titan(name='Atlas')
        prometheus = make_titan(name='Prometheus')
        relationships = []
        gods = []
        titans = [
            {'expected_slug': atlas.slug, 'siblings': ['prometheus'], 'weapon_slugs': []},
            {'expected_slug': prometheus.slug, 'siblings': ['atlas'], 'weapon_slugs': []},
        ]

        with TemporaryDirectory() as temp_dir:
            files = {
                'divine_relationships.json': relationships,
                'gods.json': gods,
                'titans.json': titans,
            }
            paths = {}
            for name, contents in files.items():
                path = Path(temp_dir) / name
                path.write_text(json.dumps(contents), encoding='utf-8')
                paths[name] = path
            output = StringIO()
            with (
                patch(
                    'apps.divinities.management.commands.seed_divine_relationships.DATA_FILE',
                    paths['divine_relationships.json'],
                ),
                patch(
                    'apps.divinities.management.commands.seed_divine_relationships.GODS_FILE',
                    paths['gods.json'],
                ),
                patch(
                    'apps.divinities.management.commands.seed_divine_relationships.TITANS_FILE',
                    paths['titans.json'],
                ),
            ):
                call_command('seed_divine_relationships', stdout=output)

        self.assertEqual(
            DivineRelationship.objects.filter(relationship_type='sibling_of').count(), 1
        )
        self.assertIn('Sibling links synchronized: 1.', output.getvalue())

    def test_unresolved_entity_warns_and_skips_only_the_relationship(self):
        data = [
            {
                'from_type': 'titan',
                'from_slug': 'missing-titan',
                'to_type': 'character',
                'to_slug': 'missing-character',
                'relationship_type': 'parent_of',
            }
        ]

        with TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / 'divine_relationships.json'
            gods_file = Path(temp_dir) / 'gods.json'
            titans_file = Path(temp_dir) / 'titans.json'
            data_file.write_text(json.dumps(data), encoding='utf-8')
            gods_file.write_text('[]', encoding='utf-8')
            titans_file.write_text('[]', encoding='utf-8')
            output = StringIO()
            with (
                patch(
                    'apps.divinities.management.commands.seed_divine_relationships.DATA_FILE',
                    data_file,
                ),
                patch(
                    'apps.divinities.management.commands.seed_divine_relationships.GODS_FILE',
                    gods_file,
                ),
                patch(
                    'apps.divinities.management.commands.seed_divine_relationships.TITANS_FILE',
                    titans_file,
                ),
            ):
                call_command('seed_divine_relationships', stdout=output)

        self.assertEqual(DivineRelationship.objects.count(), 0)
        self.assertEqual(output.getvalue().count('[WARN]'), 2)
        self.assertIn("Unresolved titan 'missing-titan'", output.getvalue())
        self.assertIn("Unresolved character 'missing-character'", output.getvalue())


class MissingBookSlugWarningTests(TestCase):
    def test_missing_book_slugs_warn_and_skip_only_missing_references(self):
        valid_book = make_book(title='Valid Book', book_number=1)
        god = make_god(
            name='Zeus',
            first_appearance_book=valid_book,
            wiki_url='https://riordan.fandom.com/wiki/Existing_Zeus',
        )
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
        self.assertEqual(god.wiki_url, 'https://riordan.fandom.com/wiki/Existing_Zeus')
        self.assertEqual(list(god.books_appeared_in.all()), [valid_book])
        self.assertEqual(output.getvalue().count('Warning:'), 2)
        self.assertIn('Gods seeded: 0 created, 1 updated, 0 errors.', output.getvalue())
