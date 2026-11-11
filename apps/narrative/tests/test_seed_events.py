import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.narrative.models import Event, EventCasualty
from tests.makers import make_event


class SeedEventsCommandTests(TestCase):
    seed_commands = (
        'seed_books',
        'seed_gods',
        'seed_titans',
        'seed_characters',
        'seed_monsters',
        'seed_locations',
        'seed_events',
    )

    def seed_all(self):
        outputs = []
        for command in self.seed_commands:
            output = StringIO()
            call_command(command, stdout=output)
            outputs.append(output.getvalue())
        return outputs

    def test_seed_events_resolves_references_and_is_idempotent(self):
        outputs = self.seed_all()

        self.assertEqual(Event.objects.count(), 23)
        self.assertEqual(Event.objects.filter(wiki_url__isnull=False).count(), 21)
        self.assertEqual(
            Event.objects.get(slug='battle-of-the-st-louis-arch').wiki_url,
            'https://riordan.fandom.com/wiki/The_Last_Olympian#The_River_Styx',
        )
        self.assertEqual(EventCasualty.objects.count(), 13)
        self.assertEqual(
            sum(event.participant_characters.count() for event in Event.objects.all()),
            86,
        )
        output = outputs[-1]
        self.assertEqual(output.count('[WARN]'), 2)
        self.assertIn("Unresolved titan participant 'coeus'", output)
        self.assertIn("Unresolved titan participant 'crius'", output)
        self.assertNotIn("Unresolved location 'land-without-rain'", output)
        self.assertFalse(any('[WARN]' in value for value in outputs[:-1]))

        titanomachy = Event.objects.get(slug='first-titanomachy')
        self.assertEqual(titanomachy.in_universe_timeframe, 'Ancient Mythological Era')
        self.assertEqual(titanomachy.date_precision, 'mythological_era')
        self.assertEqual(titanomachy.chronology_order, 10)
        self.assertIn('kampe', titanomachy.participant_monsters.values_list('slug', flat=True))
        kampe_casualty = titanomachy.casualty_records.get(casualty_monster__slug='kampe')
        self.assertEqual(kampe_casualty.casualty_monster.name, 'Kampê')

        times_square = Event.objects.get(slug='battle-of-times-square')
        self.assertEqual(times_square.book.slug, 'percy-jackson-and-the-singer-of-apollo')
        self.assertIn('celedon', times_square.participant_characters.values_list('slug', flat=True))
        self.assertFalse(times_square.participant_monsters.filter(slug='celedon').exists())

        sacrifice_event = Event.objects.get(slug='destruction-of-the-talos-automaton')
        self.assertEqual(sacrifice_event.location.slug, 'land-without-rain')
        beckendorfs_sacrifice = Event.objects.get(slug='beckendorfs-sacrifice')
        self.assertEqual(beckendorfs_sacrifice.in_universe_timeframe, 'August 12 (Percy Age 15)')
        self.assertEqual(beckendorfs_sacrifice.date_precision, 'exact')
        self.assertEqual(beckendorfs_sacrifice.chronology_order, 170)

        rerun = StringIO()
        call_command('seed_events', stdout=rerun)
        self.assertEqual(Event.objects.count(), 23)
        self.assertEqual(EventCasualty.objects.count(), 13)
        self.assertIn('23 updated', rerun.getvalue())

    def test_null_wiki_url_does_not_clear_existing_event_url(self):
        event = make_event(
            name='First Titanomachy',
            wiki_url='https://riordan.fandom.com/wiki/Existing_Event',
        )
        entry = {
            'name': event.name,
            'expected_slug': event.slug,
            'event_type': 'battle',
            'wiki_url': None,
        }
        with TemporaryDirectory() as directory:
            data_file = Path(directory) / 'events.json'
            data_file.write_text(json.dumps([entry]), encoding='utf-8')
            output = StringIO()
            with patch('apps.narrative.management.commands.seed_events.DATA_FILE', data_file):
                call_command('seed_events', stdout=output)

        self.assertIn('Events seeded: 0 created, 1 updated, 0 errors.', output.getvalue())
        self.assertNotIn('[WARN]', output.getvalue())

        event.refresh_from_db()
        self.assertEqual(event.wiki_url, 'https://riordan.fandom.com/wiki/Existing_Event')

    def test_unresolved_references_warn_and_are_skipped(self):
        entry = {
            'name': 'Unresolved Event',
            'expected_slug': 'unresolved-event',
            'event_type': 'battle',
            'book_slug': 'missing-book',
            'location_slug': 'missing-location',
            'participants': [{'type': 'monster', 'slug': 'missing-monster'}],
            'casualties': [{'type': 'character', 'slug': 'missing-character'}],
        }
        with TemporaryDirectory() as directory:
            data_file = Path(directory) / 'events.json'
            data_file.write_text(json.dumps([entry]), encoding='utf-8')
            output = StringIO()
            with patch('apps.narrative.management.commands.seed_events.DATA_FILE', data_file):
                call_command('seed_events', stdout=output)

        event = Event.objects.get(slug='unresolved-event')
        self.assertIsNone(event.book)
        self.assertIsNone(event.location)
        self.assertEqual(event.participant_monsters.count(), 0)
        self.assertEqual(event.casualty_records.count(), 0)
        self.assertEqual(output.getvalue().count('[WARN]'), 4)
        self.assertIn('0 errors', output.getvalue())
