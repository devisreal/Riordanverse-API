from django.test import TestCase

from apps.bestiary.serializers import MonsterDetailSerializer
from tests.makers import make_character, make_monster


class MonsterDetailSerializerTests(TestCase):
    def setUp(self):
        self.monster = make_monster(name='Medusa', monster_type='gorgon')

    def test_defeated_by_slugs_empty(self):
        data = MonsterDetailSerializer(self.monster).data
        self.assertEqual(data['defeated_by_slugs'], [])

    def test_defeated_by_slugs_populated(self):
        percy = make_character(name='Percy Jackson')
        self.monster.defeated_by.add(percy)
        data = MonsterDetailSerializer(self.monster).data
        self.assertIn('percy-jackson', data['defeated_by_slugs'])

    def test_monster_type_display(self):
        data = MonsterDetailSerializer(self.monster).data
        self.assertEqual(data['monster_type_display'], 'Gorgon')

    def test_aliases_field(self):
        self.monster.aliases = ['Aunty Em']
        self.monster.save()
        data = MonsterDetailSerializer(self.monster).data
        self.assertIn('Aunty Em', data['aliases'])
