from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from tests.makers import (
    make_character,
    make_divine_relationship,
    make_god,
    make_titan,
    make_weapon,
)


class GodListViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.poseidon = make_god(name='Poseidon', tier='olympian', is_big_three=True)

    def test_list_returns_200_and_paginated_envelope(self):
        response = self.client.get(reverse('god-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.data)
        self.assertIn('meta', response.data)

    def test_detail_returns_200(self):
        response = self.client.get(reverse('god-detail', kwargs={'slug': 'poseidon'}))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_404_for_unknown(self):
        response = self.client.get(reverse('god-detail', kwargs={'slug': 'nobody'}))
        self.assertEqual(response.status_code, 404)

    def test_filter_is_big_three(self):
        make_god(name='Athena', is_big_three=False)
        response = self.client.get(reverse('god-list'), {'is_big_three': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_tier(self):
        make_god(name='Iris', tier='minor')
        response = self.client.get(reverse('god-list'), {'tier': 'olympian'})
        self.assertEqual(len(response.data['data']), 1)

    def test_invalid_tier_returns_400(self):
        response = self.client.get(reverse('god-list'), {'tier': 'supreme'})
        self.assertEqual(response.status_code, 400)

    def test_children_subresource(self):
        percy = make_character(name='Percy Jackson')
        make_divine_relationship(from_entity=self.poseidon, to_entity=percy)
        response = self.client.get(reverse('god-children-list', kwargs={'slug': 'poseidon'}))
        self.assertEqual(response.status_code, 200)
        slugs = [character['slug'] for character in response.data['data']]
        self.assertIn('percy-jackson', slugs)

    def test_weapons_subresource(self):
        trident = make_weapon(name='Trident')
        self.poseidon.weapons.add(trident)
        response = self.client.get(reverse('god-weapon-list', kwargs={'slug': 'poseidon'}))
        self.assertEqual(response.status_code, 200)
        slugs = [weapon['slug'] for weapon in response.data['data']]
        self.assertIn('trident', slugs)


class TitanListViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.kronos = make_titan(
            name='Kronos',
            alignment='kronos_army',
            status='imprisoned',
            display_order=10,
        )

    def test_list_returns_200(self):
        response = self.client.get(reverse('titan-list'))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_200(self):
        response = self.client.get(reverse('titan-detail', kwargs={'slug': 'kronos'}))
        self.assertEqual(response.status_code, 200)

    def test_list_exposes_and_defaults_to_display_order(self):
        make_titan(name='Atlas', display_order=20)

        response = self.client.get(reverse('titan-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['slug'] for item in response.data['data']], ['kronos', 'atlas'])
        self.assertEqual(response.data['data'][0]['display_order'], 10)
        self.assertEqual(response.data['data'][1]['display_order'], 20)

    def test_list_can_sort_by_display_order(self):
        make_titan(name='Atlas', display_order=20)

        response = self.client.get(
            reverse('titan-list'), {'sort': 'display_order', 'order': 'desc'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['slug'] for item in response.data['data']], ['atlas', 'kronos'])

    def test_list_places_unranked_titans_after_curated_entries(self):
        unranked = make_titan(name='Unranked Titan')

        response = self.client.get(reverse('titan-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item['slug'] for item in response.data['data']],
            [self.kronos.slug, unranked.slug],
        )

    def test_detail_includes_weapon_slugs_and_home(self):
        scythe = make_weapon(name='Kronos Scythe')
        self.kronos.weapons.add(scythe)
        self.kronos.home = 'Mount Othrys'
        self.kronos.save()

        response = self.client.get(reverse('titan-detail', kwargs={'slug': 'kronos'}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['weapon_slugs'], ['kronos-scythe'])
        self.assertEqual(response.data['home'], 'Mount Othrys')
        self.assertEqual(response.data['display_order'], 10)

    def test_filter_by_alignment(self):
        make_titan(name='Prometheus', alignment='neutral')
        response = self.client.get(reverse('titan-list'), {'alignment': 'kronos_army'})
        self.assertEqual(len(response.data['data']), 1)

    def test_invalid_alignment_returns_400(self):
        response = self.client.get(reverse('titan-list'), {'alignment': 'good-guy'})
        self.assertEqual(response.status_code, 400)
