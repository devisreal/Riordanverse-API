from django.test import TestCase

from apps.locations.serializers import LocationDetailSerializer, LocationListSerializer
from tests.makers import make_character, make_god, make_location, make_monster, make_titan


class LocationSerializerTests(TestCase):
    def test_controlled_by_god(self):
        hades = make_god(name='Hades')
        location = make_location(name='The Underworld', controlled_by_god=hades)
        data = LocationListSerializer(location).data
        self.assertEqual(data['controlled_by']['type'], 'god')
        self.assertEqual(data['controlled_by']['slug'], 'hades')

    def test_controlled_by_titan(self):
        atlas = make_titan(name='Atlas')
        location = make_location(name='Mount Othrys', controlled_by_titan=atlas)
        data = LocationListSerializer(location).data
        self.assertEqual(data['controlled_by']['type'], 'titan')
        self.assertEqual(data['controlled_by']['slug'], 'atlas')

    def test_controlled_by_character(self):
        luke = make_character(name='Luke Castellan')
        location = make_location(name='Princess Andromeda', controlled_by_character=luke)
        data = LocationListSerializer(location).data
        self.assertEqual(data['controlled_by']['type'], 'character')
        self.assertEqual(data['controlled_by']['slug'], 'luke-castellan')

    def test_controlled_by_monster(self):
        polyphemus = make_monster(name='Polyphemus')
        location = make_location(name="Polyphemus's Island", controlled_by_monster=polyphemus)
        data = LocationListSerializer(location).data
        self.assertEqual(data['controlled_by']['type'], 'monster')
        self.assertEqual(data['controlled_by']['slug'], 'polyphemus')
        self.assertEqual(data['controlled_by']['name'], 'Polyphemus')

    def test_controlled_by_null(self):
        location = make_location(name='Wild Forest')
        data = LocationListSerializer(location).data
        self.assertIsNone(data['controlled_by'])

    def test_detail_includes_notable_events(self):
        location = make_location(
            name='Camp Half-Blood',
            notable_events=['Percy arrives', 'Battle of the Labyrinth'],
        )
        data = LocationDetailSerializer(location).data
        self.assertEqual(len(data['notable_events']), 2)
