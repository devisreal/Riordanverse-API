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

    def test_sibling_relationship_is_visible_from_both_entities(self):
        apollo = make_god(name='Apollo')
        artemis = make_god(name='Artemis')
        make_divine_relationship(
            from_entity=apollo,
            to_entity=artemis,
            relationship_type='sibling_of',
        )

        self.assertEqual(GodDetailSerializer(apollo).data['siblings'][0]['slug'], 'artemis')
        self.assertEqual(GodDetailSerializer(artemis).data['siblings'][0]['slug'], 'apollo')

    def test_consort_relationship_is_visible_from_both_gods(self):
        hera = make_god(name='Hera')
        make_divine_relationship(
            from_entity=hera,
            to_entity=self.zeus,
            relationship_type='consort_of',
        )

        self.assertEqual(GodDetailSerializer(hera).data['consorts'][0]['slug'], 'zeus')
        self.assertEqual(GodDetailSerializer(self.zeus).data['consorts'][0]['slug'], 'hera')


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

    def test_sacred_animals_and_plants_are_serialized(self):
        self.kronos.sacred_animals = ['white horse']
        self.kronos.sacred_plants = ['heliotrope']
        self.kronos.save()

        data = TitanDetailSerializer(self.kronos).data
        self.assertEqual(data['sacred_animals'], ['white horse'])
        self.assertEqual(data['sacred_plants'], ['heliotrope'])

    def test_children_include_characters(self):
        phaethon = make_character(name='Phaethon')
        make_divine_relationship(from_entity=self.kronos, to_entity=phaethon)

        children = TitanDetailSerializer(self.kronos).data['children']
        phaethon_child = next(child for child in children if child['slug'] == 'phaethon')
        self.assertEqual(phaethon_child['type'], 'character')

    def test_child_of_relationships_are_serialized_as_parents(self):
        rhea = make_titan(name='Rhea', alignment='neutral')
        ouranos = make_god(name='Ouranos', tier='primordial')
        make_divine_relationship(
            from_entity=rhea,
            to_entity=ouranos,
            relationship_type='child_of',
        )

        parents = TitanDetailSerializer(rhea).data['parents']
        self.assertEqual([parent['slug'] for parent in parents], ['ouranos'])

    def test_consort_relationship_is_visible_from_both_titans(self):
        rhea = make_titan(name='Rhea', alignment='neutral')
        make_divine_relationship(
            from_entity=self.kronos,
            to_entity=rhea,
            relationship_type='consort_of',
        )

        self.assertEqual(TitanDetailSerializer(self.kronos).data['consorts'][0]['slug'], 'rhea')
        self.assertEqual(TitanDetailSerializer(rhea).data['consorts'][0]['slug'], 'kronos')
