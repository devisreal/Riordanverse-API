from django.test import TestCase

from apps.characters.serializers import CharacterDetailSerializer, CharacterListSerializer
from tests.makers import make_character, make_god, make_power


class CharacterListSerializerTests(TestCase):
    def setUp(self):
        self.poseidon = make_god(name='Poseidon')
        self.character = make_character(
            name='Percy Jackson',
            character_type='demigod',
            divine_parent=self.poseidon,
            is_big_three_child=True,
        )

    def test_expected_list_fields_are_present(self):
        data = CharacterListSerializer(self.character).data
        self.assertIn('slug', data)
        self.assertIn('name', data)
        self.assertIn('divine_parent_slug', data)
        self.assertIn('is_big_three_child', data)

    def test_divine_parent_slug(self):
        data = CharacterListSerializer(self.character).data
        self.assertEqual(data['divine_parent_slug'], 'poseidon')

    def test_divine_parent_slug_is_null_without_parent(self):
        mortal = make_character(name='Sally Jackson', character_type='mortal')
        data = CharacterListSerializer(mortal).data
        self.assertIsNone(data['divine_parent_slug'])


class CharacterDetailSerializerTests(TestCase):
    def setUp(self):
        self.poseidon = make_god(name='Poseidon')
        self.character = make_character(name='Percy Jackson', divine_parent=self.poseidon)
        make_power(
            character=self.character,
            name='Hydrokinesis',
            source='divine_parent',
        )

    def test_powers_are_nested(self):
        data = CharacterDetailSerializer(self.character).data
        self.assertEqual(len(data['powers']), 1)
        self.assertEqual(data['powers'][0]['name'], 'Hydrokinesis')

    def test_sibling_slugs_empty_by_default(self):
        data = CharacterDetailSerializer(self.character).data
        self.assertEqual(data['sibling_slugs'], [])

    def test_sibling_slugs_populated(self):
        tyson = make_character(name='Tyson')
        self.character.siblings.add(tyson)
        data = CharacterDetailSerializer(self.character).data
        self.assertIn('tyson', data['sibling_slugs'])

    def test_empathy_link_slug_is_null(self):
        data = CharacterDetailSerializer(self.character).data
        self.assertIsNone(data['empathy_link_slug'])

    def test_appearance_field(self):
        self.character.appearance = {'hair_color': 'black', 'eye_color': 'sea-green'}
        self.character.save()
        data = CharacterDetailSerializer(self.character).data
        self.assertEqual(data['appearance']['hair_color'], 'black')

    def test_special_states_field(self):
        self.character.special_states = [
            {
                'state': 'achilles_blessing',
                'description': 'Invulnerable except at the small of his back',
                'active_from_book': 5,
                'active_to_book': 5,
            }
        ]
        self.character.save()
        data = CharacterDetailSerializer(self.character).data
        self.assertEqual(len(data['special_states']), 1)
        self.assertEqual(data['special_states'][0]['state'], 'achilles_blessing')
