import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.locations.models import Location


class SeedLocationsCommandTests(TestCase):
    def test_seed_resolves_controllers_and_books_idempotently(self):
        for command in (
            'seed_books',
            'seed_gods',
            'seed_titans',
            'seed_characters',
            'seed_monsters',
        ):
            call_command(command, stdout=StringIO())

        output = StringIO()
        call_command('seed_locations', stdout=output)

        self.assertEqual(Location.objects.count(), 27)
        self.assertEqual(Location.objects.filter(wiki_url__isnull=False).count(), 25)
        manhattan = Location.objects.get(slug='manhattan')
        self.assertEqual(manhattan.location_order, 10)
        self.assertEqual(manhattan.first_appearance_book.slug, 'the-lightning-thief')
        self.assertEqual(manhattan.first_appearance_locator, 'Chapter 1')
        self.assertEqual(
            Location.objects.get(slug='camp-half-blood').wiki_url,
            'https://riordan.fandom.com/wiki/Camp_Half-Blood',
        )
        self.assertNotIn('[WARN]', output.getvalue())

        gateway_arch = Location.objects.get(slug='gateway-arch')
        self.assertEqual(gateway_arch.controlled_by_monster.slug, 'echidna')
        labyrinth = Location.objects.get(slug='the-labyrinth')
        self.assertEqual(labyrinth.controlled_by_character.slug, 'daedalus')
        tartarus = Location.objects.get(slug='tartarus')
        self.assertEqual(tartarus.controlled_by_god.slug, 'tartarus')
        self.assertIsNone(tartarus.controlled_by_titan)
        brooklyn_zoo = Location.objects.get(slug='brooklyn-zoo')
        self.assertIsNone(brooklyn_zoo.wiki_url)
        self.assertEqual(
            brooklyn_zoo.first_appearance_book.slug,
            'percy-jackson-and-the-stolen-chariot',
        )
        self.assertEqual(brooklyn_zoo.location_order, 260)
        self.assertIn(
            'percy-jackson-and-the-stolen-chariot',
            brooklyn_zoo.books_appeared_in.values_list('slug', flat=True),
        )
        seriphos = Location.objects.get(slug='seriphos')
        self.assertIn(
            'percy-jacksons-greek-heroes',
            seriphos.books_appeared_in.values_list('slug', flat=True),
        )
        land_without_rain = Location.objects.get(slug='land-without-rain')
        self.assertEqual(land_without_rain.controlled_by_god.slug, 'hephaestus')
        self.assertIn(
            'the-titans-curse',
            land_without_rain.books_appeared_in.values_list('slug', flat=True),
        )
        camp = Location.objects.get(slug='camp-half-blood')
        self.assertIn(
            'the-last-olympian',
            camp.books_appeared_in.values_list('slug', flat=True),
        )
        self.assertEqual(camp.first_appearance_locator, 'Chapter 5')
        self.assertEqual(camp.earlier_mention_book.slug, 'the-lightning-thief')
        self.assertEqual(camp.location_order, 20)

        rerun = StringIO()
        call_command('seed_locations', stdout=rerun)
        self.assertEqual(Location.objects.count(), 27)
        self.assertIn('27 updated', rerun.getvalue())

    def test_seed_uses_explicit_expected_slug(self):
        entry = {
            'name': 'Canonical Test Place',
            'expected_slug': 'master-slug',
            'location_type': 'mortal_city',
            'books_appeared_in_slugs': [],
        }
        with TemporaryDirectory() as directory:
            data_file = Path(directory) / 'locations.json'
            data_file.write_text(json.dumps([entry]), encoding='utf-8')
            with patch('apps.locations.management.commands.seed_locations.DATA_FILE', data_file):
                call_command('seed_locations', stdout=StringIO())

        self.assertTrue(Location.objects.filter(slug='master-slug').exists())
        self.assertFalse(Location.objects.filter(slug='canonical-test-place').exists())

    def test_unresolved_first_appearance_books_warn_and_remain_null(self):
        entry = {
            'name': 'Unresolved Appearance Place',
            'expected_slug': 'unresolved-appearance-place',
            'location_type': 'mortal_city',
            'first_appearance_book_slug': 'missing-first-book',
            'earlier_mention_book_slug': 'missing-earlier-book',
            'books_appeared_in_slugs': [],
        }
        with TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / 'locations.json'
            data_file.write_text(json.dumps([entry]), encoding='utf-8')
            output = StringIO()
            with patch('apps.locations.management.commands.seed_locations.DATA_FILE', data_file):
                call_command('seed_locations', stdout=output)

        location = Location.objects.get(slug='unresolved-appearance-place')
        self.assertIsNone(location.first_appearance_book)
        self.assertIsNone(location.earlier_mention_book)
        self.assertEqual(output.getvalue().count('[WARN]'), 2)
        self.assertIn('0 errors', output.getvalue())

    def test_null_wiki_url_does_not_clear_existing_location_url(self):
        location = Location.objects.create(
            name='Unlisted Place',
            wiki_url='https://riordan.fandom.com/wiki/Existing_Place',
        )
        entry = {
            'name': location.name,
            'expected_slug': location.slug,
            'wiki_url': None,
            'books_appeared_in_slugs': [],
        }

        with TemporaryDirectory() as directory:
            data_file = Path(directory) / 'locations.json'
            data_file.write_text(json.dumps([entry]), encoding='utf-8')
            with patch('apps.locations.management.commands.seed_locations.DATA_FILE', data_file):
                call_command('seed_locations', stdout=StringIO())

        location.refresh_from_db()
        self.assertEqual(location.wiki_url, 'https://riordan.fandom.com/wiki/Existing_Place')
