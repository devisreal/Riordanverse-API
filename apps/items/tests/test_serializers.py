from django.test import TestCase

from apps.items.serializers import WeaponDetailSerializer, WeaponListSerializer
from tests.makers import make_character, make_god, make_weapon


class WeaponListSerializerTests(TestCase):
    def test_character_owner_shape(self):
        percy = make_character(name='Percy Jackson')
        weapon = make_weapon(name='Riptide', owner_primary_character=percy)
        data = WeaponListSerializer(weapon).data
        self.assertEqual(data['owner_primary']['type'], 'character')
        self.assertEqual(data['owner_primary']['slug'], 'percy-jackson')

    def test_god_owner_shape(self):
        zeus = make_god(name='Zeus')
        weapon = make_weapon(name='Lightning Bolt', owner_primary_god=zeus)
        data = WeaponListSerializer(weapon).data
        self.assertEqual(data['owner_primary']['type'], 'god')
        self.assertEqual(data['owner_primary']['slug'], 'zeus')

    def test_owner_is_null_for_unclaimed_weapon(self):
        weapon = make_weapon(name='Unclaimed')
        data = WeaponListSerializer(weapon).data
        self.assertIsNone(data['owner_primary'])


class WeaponDetailSerializerTests(TestCase):
    def test_owner_history_field(self):
        weapon = make_weapon(
            name='Riptide',
            owner_history=[{'type': 'god', 'slug': 'poseidon', 'notes': 'Original owner'}],
        )
        data = WeaponDetailSerializer(weapon).data
        self.assertIn('owner_history', data)
        self.assertEqual(len(data['owner_history']), 1)
        self.assertEqual(data['owner_history'][0]['slug'], 'poseidon')

    def test_forged_by_slug_is_null(self):
        weapon = make_weapon(name='Mystery Weapon')
        data = WeaponDetailSerializer(weapon).data
        self.assertIsNone(data['forged_by_slug'])

    def test_forged_by_slug(self):
        hephaestus = make_god(name='Hephaestus')
        weapon = make_weapon(name='Divine Sword', forged_by=hephaestus)
        data = WeaponDetailSerializer(weapon).data
        self.assertEqual(data['forged_by_slug'], 'hephaestus')
