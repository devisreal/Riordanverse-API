from django.test import TestCase

from apps.characters.serializers import CharacterDetailSerializer, CharacterListSerializer
from tests.makers import (
    make_book,
    make_character,
    make_divine_relationship,
    make_god,
    make_power,
    make_titan,
)


class CharacterListSerializerTests(TestCase):
    def setUp(self):
        self.poseidon = make_god(name='Poseidon')
        self.character = make_character(
            name='Percy Jackson',
            character_type='demigod',
            is_big_three_child=True,
            divine_parent=self.poseidon,
        )
        make_divine_relationship(from_entity=self.poseidon, to_entity=self.character)

    def test_expected_list_fields_are_present(self):
        data = CharacterListSerializer(self.character).data
        self.assertIn('slug', data)
        self.assertIn('name', data)
        self.assertEqual(data['divine_parent_slug'], 'poseidon')
        self.assertNotIn('type', data)
        self.assertNotIn('family', data)
        self.assertIn('is_big_three_child', data)

    def test_family_is_empty_without_relationships(self):
        mortal = make_character(name='Sally Jackson', character_type='mortal')
        data = CharacterListSerializer(mortal).data
        self.assertIsNone(data['divine_parent_slug'])
        self.assertNotIn('family', data)


class CharacterDetailSerializerTests(TestCase):
    def setUp(self):
        self.poseidon = make_god(name='Poseidon')
        self.character = make_character(name='Percy Jackson')
        make_divine_relationship(from_entity=self.poseidon, to_entity=self.character)
        make_power(
            character=self.character,
            name='Hydrokinesis',
            source='divine_parent',
        )

    def test_powers_are_nested(self):
        data = CharacterDetailSerializer(self.character).data
        self.assertEqual(len(data['powers']), 1)
        self.assertEqual(data['powers'][0]['name'], 'Hydrokinesis')

    def test_power_wiki_url_is_exposed_in_character_detail(self):
        power = self.character.powers.get(name='Hydrokinesis')
        power.wiki_url = 'https://riordan.fandom.com/wiki/Hydrokinesis'
        power.save(update_fields=['wiki_url'])

        data = CharacterDetailSerializer(self.character).data

        self.assertEqual(
            data['powers'][0]['wiki_url'],
            'https://riordan.fandom.com/wiki/Hydrokinesis',
        )

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

    def test_family_is_nested_with_empty_sibling_array_by_default(self):
        data = CharacterDetailSerializer(self.character).data
        self.assertEqual(data['family']['siblings'], [])
        self.assertNotIn('sibling_slugs', data)
        self.assertNotIn('divine_parent_slug', data)

    def test_siblings_are_nested_typed_references(self):
        tyson = make_character(name='Tyson')
        make_divine_relationship(
            from_entity=self.character, to_entity=tyson, relationship_type='sibling_of'
        )
        data = CharacterDetailSerializer(self.character).data
        self.assertEqual(data['family']['siblings'][0]['slug'], 'tyson')

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

        make_divine_relationship(from_entity=helios, to_entity=phaethon)
        data = CharacterDetailSerializer(phaethon).data
        self.assertEqual(data['family']['parents'][0]['slug'], 'helios')
        self.assertEqual(data['family']['parents'][0]['type'], 'titan')
