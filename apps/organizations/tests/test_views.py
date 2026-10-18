from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from tests.makers import make_cabin, make_faction, make_god


class CabinViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.god = make_god(name='Poseidon')
        self.cabin = make_cabin(number=3, deity=self.god)

    def test_list_returns_200(self):
        response = self.client.get(reverse('cabin-list'))
        self.assertEqual(response.status_code, 200)

    def test_list_returns_paginated_data_envelope(self):
        response = self.client.get(reverse('cabin-list'))
        self.assertIn('data', response.data)
        self.assertIn('meta', response.data)

    def test_list_contains_cabin(self):
        response = self.client.get(reverse('cabin-list'))
        slugs = [cabin['slug'] for cabin in response.data['data']]
        self.assertIn('cabin-3-poseidon', slugs)

    def test_detail_returns_200(self):
        response = self.client.get(reverse('cabin-detail', kwargs={'slug': self.cabin.slug}))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_404_for_unknown_slug(self):
        response = self.client.get(reverse('cabin-detail', kwargs={'slug': 'cabin-99-nobody'}))
        self.assertEqual(response.status_code, 404)

    def test_number_lookup_returns_cabin(self):
        response = self.client.get(reverse('cabin-by-number', kwargs={'number': 3}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['slug'], 'cabin-3-poseidon')

    def test_number_lookup_returns_404_for_unknown_number(self):
        response = self.client.get(reverse('cabin-by-number', kwargs={'number': 99}))
        self.assertEqual(response.status_code, 404)

    def test_filter_is_honorary_true(self):
        make_cabin(number=2, deity=None, is_honorary=True)
        response = self.client.get(reverse('cabin-list'), {'is_honorary': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_is_honorary_false(self):
        make_cabin(number=2, deity=None, is_honorary=True)
        response = self.client.get(reverse('cabin-list'), {'is_honorary': 'false'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_invalid_position_filter_returns_400(self):
        response = self.client.get(reverse('cabin-list'), {'position': 'diagonal'})
        self.assertEqual(response.status_code, 400)

    def test_ordering_by_number(self):
        make_cabin(number=1, deity=make_god(name='Zeus'))
        response = self.client.get(reverse('cabin-list'), {'ordering': 'number'})
        numbers = [cabin['number'] for cabin in response.data['data']]
        self.assertEqual(numbers, sorted(numbers))


class FactionViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.god = make_god(name='Artemis')
        self.faction = make_faction(
            name='Hunters of Artemis',
            alignment='olympian',
            leader_god=self.god,
        )

    def test_list_returns_200_and_paginated_envelope(self):
        response = self.client.get(reverse('faction-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.data)
        self.assertIn('meta', response.data)

    def test_detail_returns_200(self):
        response = self.client.get(reverse('faction-detail', kwargs={'slug': self.faction.slug}))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_404_for_unknown_slug(self):
        response = self.client.get(reverse('faction-detail', kwargs={'slug': 'nobody-here'}))
        self.assertEqual(response.status_code, 404)

    def test_filter_by_alignment(self):
        make_faction(name='Titan Army', alignment='titan')
        response = self.client.get(reverse('faction-list'), {'alignment': 'olympian'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_invalid_alignment_filter_returns_400(self):
        response = self.client.get(reverse('faction-list'), {'alignment': 'chaotic-neutral'})
        self.assertEqual(response.status_code, 400)

    def test_detail_flattens_leader(self):
        response = self.client.get(reverse('faction-detail', kwargs={'slug': self.faction.slug}))
        self.assertEqual(
            response.data['leader'],
            {'type': 'god', 'slug': 'artemis', 'name': 'Artemis'},
        )
