from django.core.management import BaseCommand, call_command

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


class Command(BaseCommand):
    help = 'Run all canonical seed commands in dependency order.'

    def handle(self, *args, **options):
        for command in SEED_COMMANDS:
            self.stdout.write(f'Running {command}...')
            call_command(command, stdout=self.stdout, stderr=self.stderr)

        self.stdout.write(self.style.SUCCESS('All canonical seed commands completed.'))
