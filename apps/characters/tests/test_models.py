from django.test import TestCase

from apps.characters.models import Power
from tests.makers import make_character, make_god, make_power


class CharacterModelTests(TestCase):
    def setUp(self):
        self.character = make_character(name='Percy Jackson')

    def test_string_representation(self):
        self.assertEqual(str(self.character), 'Percy Jackson')

    def test_slug_generated(self):
        self.assertEqual(self.character.slug, 'percy-jackson')

    def test_aliases_default_to_empty_list(self):
        self.assertEqual(self.character.aliases, [])

    def test_aliases_accept_a_list(self):
        self.character.aliases = ['Seaweed Brain', 'Son of the Sea God']
        self.character.save()
        self.character.refresh_from_db()
        self.assertEqual(len(self.character.aliases), 2)

    def test_affiliation_defaults_to_empty_list(self):
        self.assertEqual(self.character.affiliation, [])

    def test_special_states_default_to_empty_list(self):
        self.assertEqual(self.character.special_states, [])

    def test_appearance_defaults_to_empty_dict(self):
        self.assertEqual(self.character.appearance, {})

    def test_divine_parent_is_nullable(self):
        self.assertIsNone(self.character.divine_parent)

    def test_divine_parent_can_be_set(self):
        poseidon = make_god(name='Poseidon')
        self.character.divine_parent = poseidon
        self.character.save()
        self.character.refresh_from_db()
        self.assertEqual(self.character.divine_parent, poseidon)

    def test_siblings_many_to_many_is_symmetrical(self):
        tyson = make_character(name='Tyson')
        self.character.siblings.add(tyson)
        self.assertIn(tyson, self.character.siblings.all())
        self.assertIn(self.character, tyson.siblings.all())

    def test_empathy_link_one_to_one(self):
        grover = make_character(name='Grover Underwood')
        self.character.empathy_link = grover
        self.character.save()
        self.assertEqual(self.character.empathy_link, grover)
        self.assertEqual(grover.empathy_link_partner, self.character)

    def test_is_demigod_defaults_true(self):
        self.assertTrue(self.character.is_demigod)

    def test_tyson_can_be_non_demigod(self):
        tyson = make_character(
            name='Tyson',
            character_type='cyclops',
            is_demigod=False,
        )
        self.assertFalse(tyson.is_demigod)


class PowerModelTests(TestCase):
    def setUp(self):
        self.character = make_character(name='Percy Jackson')
        self.power = make_power(
            character=self.character,
            name='Hydrokinesis',
            source='divine_parent',
        )

    def test_string_representation(self):
        self.assertEqual(str(self.power), 'Percy Jackson — Hydrokinesis')

    def test_scope_defaults_to_empty_list(self):
        self.assertEqual(self.power.scope, [])

    def test_power_belongs_to_character(self):
        self.assertEqual(self.power.character, self.character)

    def test_power_classification_and_lore_defaults(self):
        self.assertEqual(self.power.type, 'utility')
        self.assertFalse(self.power.is_passive)
        self.assertFalse(self.power.is_book_specific)
        self.assertEqual(self.power.display_order, 0)

    def test_character_power_reverse_relation(self):
        self.assertIn(self.power, self.character.powers.all())

    def test_power_is_deleted_with_character(self):
        self.character.delete()
        self.assertFalse(Power.objects.filter(name='Hydrokinesis').exists())
