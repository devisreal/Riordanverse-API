from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from tests.makers import make_book, make_god, make_location, make_monster


class LocationListViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.hades = make_god(name='Hades')
        self.book = make_book(title='The Lightning Thief', book_number=1)
        self.location = make_location(
            name='The Underworld',
            location_type='underworld',
            is_hidden_from_mortals=True,
            controlled_by_god=self.hades,
            first_appearance_book=self.book,
            first_appearance_locator='Chapter 18',
            earlier_mention_book=self.book,
            location_order=70,
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

    def test_detail_returns_first_appearance_metadata(self):
        response = self.client.get(reverse('location-detail', kwargs={'slug': self.location.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['first_appearance_book_slug'], self.book.slug)
        self.assertEqual(response.data['first_appearance_locator'], 'Chapter 18')
        self.assertEqual(response.data['earlier_mention_book_slug'], self.book.slug)
        self.assertEqual(response.data['location_order'], 70)

    def test_list_defaults_to_first_appearance_order_and_supports_sort(self):
        first = make_location(name='Manhattan', location_order=10)

        response = self.client.get(reverse('location-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item['slug'] for item in response.data['data']], [first.slug, self.location.slug]
        )

        reversed_response = self.client.get(
            reverse('location-list'), {'sort': 'location_order', 'order': 'desc'}
        )
        self.assertEqual(
            [item['slug'] for item in reversed_response.data['data']],
            [self.location.slug, first.slug],
        )

    def test_filter_by_first_appearance_book(self):
        make_location(name='Another Place')

        response = self.client.get(
            reverse('location-list'), {'first_appearance_book': self.book.slug}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['slug'] for item in response.data['data']], [self.location.slug])

    def test_list_places_unranked_locations_after_curated_entries(self):
        unranked = make_location(name='Unranked Location')

        response = self.client.get(reverse('location-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item['slug'] for item in response.data['data']],
            [self.location.slug, unranked.slug],
        )

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
