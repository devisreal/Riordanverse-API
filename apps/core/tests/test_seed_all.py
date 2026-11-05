from io import StringIO
from unittest.mock import patch

from django.core.management import call_command, get_commands
from django.core.management.base import CommandError
from django.test import SimpleTestCase

SEED_COMMANDS = (
    'seed_books',
    'seed_gods',
    'seed_titans',
    'seed_characters',
    'seed_items',
    'seed_monsters',
    'seed_creatures',
    'seed_divine_relationships',
    'seed_book_relationships',
    'seed_powers',
    'seed_locations',
    'seed_cabins',
    'seed_factions',
    'seed_prophecies',
    'seed_events',
    'seed_quests',
    'seed_monster_defeats',
    'seed_images',
)


class SeedAllCommandTests(SimpleTestCase):
    def test_sequence_contains_every_registered_seed_command(self):
        registered_seed_commands = {
            name for name in get_commands() if name.startswith('seed_') and name != 'seed_all'
        }
        self.assertEqual(set(SEED_COMMANDS), registered_seed_commands)

    @patch('apps.core.management.commands.seed_all.call_command')
    def test_runs_all_seed_commands_in_dependency_order(self, mocked_call_command):
        output = StringIO()
        call_command('seed_all', stdout=output, stderr=StringIO())

        self.assertEqual(
            [invocation.args[0] for invocation in mocked_call_command.call_args_list],
            list(SEED_COMMANDS),
        )
        self.assertIn('Running seed_books...', output.getvalue())
        self.assertIn('Running seed_monster_defeats...', output.getvalue())
        self.assertIn('Running seed_images...', output.getvalue())
        self.assertIn('All canonical seed commands completed.', output.getvalue())
        self.assertTrue(
            all(
                invocation.kwargs['stdout'] is not None and invocation.kwargs['stderr'] is not None
                for invocation in mocked_call_command.call_args_list
            )
        )

    @patch('apps.core.management.commands.seed_all.call_command')
    def test_stops_when_a_seed_command_fails(self, mocked_call_command):
        mocked_call_command.side_effect = [None, CommandError('seed failure')]

        with self.assertRaisesMessage(CommandError, 'seed failure'):
            call_command('seed_all', stdout=StringIO(), stderr=StringIO())

        self.assertEqual(
            [invocation.args[0] for invocation in mocked_call_command.call_args_list],
            ['seed_books', 'seed_gods'],
        )
