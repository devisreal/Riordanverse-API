from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.bestiary.models import Creature, CreatureMember


class SeedCreaturesCommandTests(TestCase):
    def test_seed_resolves_typed_members_and_is_idempotent(self):
        for command in ('seed_books', 'seed_gods', 'seed_titans'):
            call_command(command, stdout=StringIO())
        character_output = StringIO()
        monster_output = StringIO()
        call_command('seed_characters', stdout=character_output)
        call_command('seed_monsters', stdout=monster_output)

        output = StringIO()
        call_command('seed_creatures', stdout=output)

        self.assertEqual(Creature.objects.count(), 16)
        self.assertEqual(CreatureMember.objects.count(), 20)
        self.assertNotIn('[WARN]', character_output.getvalue())
        self.assertNotIn('[WARN]', monster_output.getvalue())
        self.assertNotIn('[WARN]', output.getvalue())

        satyr = Creature.objects.get(slug='satyr')
        self.assertEqual(satyr.alignment, 'olympian')
        self.assertEqual(satyr.notable_members.count(), 5)
        self.assertIn('gleeson-hedge', satyr.notable_members.values_list('slug', flat=True))

        cyclops = Creature.objects.get(slug='cyclops')
        self.assertEqual(list(cyclops.notable_members.values_list('slug', flat=True)), ['tyson'])
        self.assertEqual(
            cyclops.member_records.get(member_monster__slug='polyphemus').member_monster.name,
            'Polyphemus',
        )

        fury = Creature.objects.get(slug='fury')
        self.assertEqual(
            fury.member_records.get(member_monster__slug='alecto').member_monster.name,
            'Alecto',
        )
        pegasus = Creature.objects.get(slug='pegasus')
        self.assertEqual(pegasus.notable_members.count(), 3)

        rerun = StringIO()
        call_command('seed_creatures', stdout=rerun)
        self.assertEqual(Creature.objects.count(), 16)
        self.assertEqual(CreatureMember.objects.count(), 20)
        self.assertEqual(satyr.notable_members.count(), 5)
        self.assertIn('16 updated', rerun.getvalue())
