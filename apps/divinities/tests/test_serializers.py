from django.test import TestCase

from apps.divinities.serializers import GodDetailSerializer, TitanDetailSerializer
from tests.makers import make_character, make_divine_relationship, make_god, make_titan


class GodDetailSerializerTests(TestCase):
    def setUp(self):
        self.zeus = make_god(name='Zeus', tier='olympian')
        self.kronos = make_titan(name='Kronos')
        make_divine_relationship(
            from_entity=self.kronos,
            to_entity=self.zeus,
            relationship_type='parent_of',
        )

    def test_parents_are_flattened(self):
        data = GodDetailSerializer(self.zeus).data
        self.assertEqual(len(data['parents']), 1)
        self.assertEqual(data['parents'][0]['type'], 'titan')
        self.assertEqual(data['parents'][0]['slug'], 'kronos')

    def test_children_empty_by_default(self):
        data = GodDetailSerializer(self.zeus).data
        self.assertEqual(data['children'], [])

    def test_children_demigod_slugs(self):
        percy = make_character(name='Percy Jackson')
        self.zeus.children_demigods.add(percy)
        data = GodDetailSerializer(self.zeus).data
        self.assertIn('percy-jackson', data['children_demigod_slugs'])

    def test_mythology_field_is_present(self):
        data = GodDetailSerializer(self.zeus).data
        self.assertEqual(data['mythology'], 'greek')

    def test_roman_only_flag(self):
        janus = make_god(name='Janus', roman_only=True)
        data = GodDetailSerializer(janus).data
        self.assertTrue(data['roman_only'])


class TitanDetailSerializerTests(TestCase):
    def setUp(self):
        self.kronos = make_titan(name='Kronos')
        self.zeus = make_god(name='Zeus')
        make_divine_relationship(
            from_entity=self.kronos,
            to_entity=self.zeus,
            relationship_type='parent_of',
        )

    def test_children_include_god(self):
        data = TitanDetailSerializer(self.kronos).data
        self.assertEqual(len(data['children']), 1)
        self.assertEqual(data['children'][0]['type'], 'god')
        self.assertEqual(data['children'][0]['slug'], 'zeus')

    def test_parents_empty_by_default(self):
        data = TitanDetailSerializer(self.kronos).data
        self.assertEqual(data['parents'], [])
