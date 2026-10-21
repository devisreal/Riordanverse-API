from django.test import TestCase

from apps.characters.serializers import CharacterDetailSerializer, CharacterListSerializer
from tests.makers import make_book, make_character, make_god, make_power, make_titan


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

    def test_power_classification_and_first_book_are_serialized(self):
        book = make_book(title='The Lightning Thief', book_number=1)
        power = self.character.powers.first()
        power.type = 'offensive'
        power.is_passive = True
        power.is_book_specific = True
        power.first_demonstrated_book = book
        power.display_order = 2
        power.save()

        serialized = CharacterDetailSerializer(self.character).data['powers'][0]
        self.assertEqual(serialized['type'], 'offensive')
        self.assertTrue(serialized['is_passive'])
        self.assertTrue(serialized['is_book_specific'])
        self.assertEqual(serialized['first_demonstrated_book'], 'the-lightning-thief')
        self.assertEqual(serialized['display_order'], 2)

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

    def test_special_states_preserve_descriptive_strings(self):
        self.character.special_states = ['Bore the Curse of Achilles during Book 5']
        self.character.save()
        data = CharacterDetailSerializer(self.character).data
        self.assertEqual(data['special_states'], ['Bore the Curse of Achilles during Book 5'])

    def test_titan_divine_parent_slug(self):
        helios = make_titan(name='Helios')
        phaethon = make_character(name='Phaethon', divine_parent_titan=helios)

        self.assertEqual(CharacterDetailSerializer(phaethon).data['divine_parent_slug'], 'helios')
