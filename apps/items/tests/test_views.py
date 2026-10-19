from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from tests.makers import make_character, make_weapon


class WeaponListViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.percy = make_character(name='Percy Jackson')
        self.weapon = make_weapon(
            name='Riptide',
            weapon_type='sword',
            material='celestial_bronze',
            owner_primary_character=self.percy,
        )

    def test_list_returns_200_and_paginated_envelope(self):
        response = self.client.get(reverse('weapon-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.data)
        self.assertIn('meta', response.data)

    def test_detail_returns_200(self):
        response = self.client.get(reverse('weapon-detail', kwargs={'slug': 'riptide'}))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_404_for_unknown(self):
        response = self.client.get(reverse('weapon-detail', kwargs={'slug': 'no-weapon'}))
        self.assertEqual(response.status_code, 404)

    def test_filter_by_material(self):
        make_weapon(name='Other Weapon', material='stygian_iron')
        response = self.client.get(reverse('weapon-list'), {'material': 'celestial_bronze'})
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_owner_character(self):
        response = self.client.get(reverse('weapon-list'), {'owner_character': 'percy-jackson'})
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_transforms(self):
        make_weapon(name='Static Weapon', transforms=False)
        self.weapon.transforms = True
        self.weapon.save()
        response = self.client.get(reverse('weapon-list'), {'transforms': 'true'})
        self.assertEqual(len(response.data['data']), 1)

    def test_invalid_material_returns_400(self):
        response = self.client.get(reverse('weapon-list'), {'material': 'kryptonite'})
        self.assertEqual(response.status_code, 400)
