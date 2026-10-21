from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from tests.makers import make_god, make_location, make_monster


class LocationListViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.hades = make_god(name='Hades')
        self.location = make_location(
            name='The Underworld',
            location_type='underworld',
            is_hidden_from_mortals=True,
            controlled_by_god=self.hades,
        )

    def test_list_returns_200_and_paginated_envelope(self):
        response = self.client.get(reverse('location-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.data)
        self.assertIn('meta', response.data)

    def test_detail_returns_200(self):
        response = self.client.get(reverse('location-detail', kwargs={'slug': 'the-underworld'}))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_404_for_unknown(self):
        response = self.client.get(reverse('location-detail', kwargs={'slug': 'no-place'}))
        self.assertEqual(response.status_code, 404)

    def test_filter_by_location_type(self):
        make_location(name='Camp Half-Blood', location_type='camp')
        response = self.client.get(reverse('location-list'), {'location_type': 'underworld'})
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_is_hidden_from_mortals(self):
        make_location(name='New York', is_hidden_from_mortals=False)
        response = self.client.get(reverse('location-list'), {'is_hidden_from_mortals': 'true'})
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_controlling_god(self):
        response = self.client.get(reverse('location-list'), {'controlled_by_god': 'hades'})
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_controlling_monster(self):
        polyphemus = make_monster(name='Polyphemus')
        location = make_location(name="Polyphemus's Island", controlled_by_monster=polyphemus)
        response = self.client.get(
            reverse('location-list'), {'controlled_by_monster': 'polyphemus'}
        )
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['slug'], location.slug)

    def test_invalid_location_type_returns_400(self):
        response = self.client.get(reverse('location-list'), {'location_type': 'space'})
        self.assertEqual(response.status_code, 400)
