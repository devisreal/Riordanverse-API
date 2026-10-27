from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from tests.makers import make_character


class SortOrderingFilterTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        make_character(name='Annabeth Chase')
        make_character(name='Percy Jackson')

    def character_names(self, response):
        return [character['name'] for character in response.data['data']]

    def test_sort_defaults_to_ascending(self):
        response = self.client.get(reverse('character-list'), {'sort': 'name'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.character_names(response), ['Annabeth Chase', 'Percy Jackson'])

    def test_order_desc_sorts_descending(self):
        response = self.client.get(
            reverse('character-list'),
            {'sort': 'name', 'order': 'desc'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.character_names(response), ['Percy Jackson', 'Annabeth Chase'])

    def test_sort_and_order_take_precedence_over_legacy_ordering(self):
        response = self.client.get(
            reverse('character-list'),
            {'sort': 'name', 'order': 'asc', 'ordering': '-name'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.character_names(response), ['Annabeth Chase', 'Percy Jackson'])

    def test_legacy_ordering_parameter_remains_supported(self):
        response = self.client.get(reverse('character-list'), {'ordering': '-name'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.character_names(response), ['Percy Jackson', 'Annabeth Chase'])

    def test_unknown_sort_field_returns_bad_request(self):
        response = self.client.get(reverse('character-list'), {'sort': 'not_a_field'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error']['code'], 'BAD_REQUEST')
        self.assertIn('not_a_field', response.data['error']['message'])

    def test_invalid_order_direction_returns_bad_request(self):
        response = self.client.get(
            reverse('character-list'),
            {'sort': 'name', 'order': 'descending'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error']['code'], 'BAD_REQUEST')

    def test_order_requires_sort(self):
        response = self.client.get(reverse('character-list'), {'order': 'desc'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error']['code'], 'BAD_REQUEST')
