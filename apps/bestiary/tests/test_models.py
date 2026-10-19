from django.test import TestCase

from tests.makers import make_character, make_creature, make_monster


class MonsterModelTests(TestCase):
    def setUp(self):
        self.monster = make_monster(
            name='Medusa',
            monster_type='gorgon',
            allegiance='independent',
        )

    def test_string_representation(self):
        self.assertEqual(str(self.monster), 'Medusa')

    def test_slug_generated(self):
        self.assertEqual(self.monster.slug, 'medusa')

    def test_aliases_default_to_empty_list(self):
        self.assertEqual(self.monster.aliases, [])

    def test_aliases_accept_a_list(self):
        self.monster.aliases = ['Aunty Em']
        self.monster.save()
        self.monster.refresh_from_db()
        self.assertEqual(self.monster.aliases, ['Aunty Em'])

    def test_can_reform_defaults_true(self):
        self.assertTrue(self.monster.can_reform)

    def test_defeated_by_many_to_many_reverse_relation(self):
        percy = make_character(name='Percy Jackson')
        self.monster.defeated_by.add(percy)
        self.assertIn(percy, self.monster.defeated_by.all())
        self.assertIn(self.monster, percy.monsters_defeated.all())


class CreatureModelTests(TestCase):
    def setUp(self):
        self.creature = make_creature(name='Satyr', alignment='olympian')

    def test_string_representation(self):
        self.assertEqual(str(self.creature), 'Satyr')

    def test_slug_generated(self):
        self.assertEqual(self.creature.slug, 'satyr')

    def test_notable_members_many_to_many(self):
        grover = make_character(name='Grover Underwood')
        self.creature.notable_members.add(grover)
        self.assertIn(grover, self.creature.notable_members.all())
