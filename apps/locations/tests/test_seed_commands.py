from io import StringIO

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

        self.assertEqual(Location.objects.count(), 24)
        self.assertNotIn('[WARN]', output.getvalue())

        gateway_arch = Location.objects.get(slug='gateway-arch')
        self.assertEqual(gateway_arch.controlled_by_monster.slug, 'echidna')
        labyrinth = Location.objects.get(slug='the-labyrinth')
        self.assertEqual(labyrinth.controlled_by_character.slug, 'daedalus')
        tartarus = Location.objects.get(slug='tartarus')
        self.assertEqual(tartarus.controlled_by_god.slug, 'tartarus')
        self.assertIsNone(tartarus.controlled_by_titan)
        self.assertIn(
            'the-last-olympian',
            Location.objects.get(slug='camp-half-blood').books_appeared_in.values_list(
                'slug', flat=True
            ),
        )

        rerun = StringIO()
        call_command('seed_locations', stdout=rerun)
        self.assertEqual(Location.objects.count(), 24)
        self.assertIn('24 updated', rerun.getvalue())
