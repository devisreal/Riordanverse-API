from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from tests.makers import make_character


class StrictBooleanFilterTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        make_character(name='Percy Jackson', is_demigod=True)
        make_character(
            name='Tyson',
            character_type='cyclops',
            species='cyclops',
            is_demigod=False,
        )

    def test_lowercase_true_and_false_filter_values(self):
        true_response = self.client.get(reverse('character-list'), {'is_demigod': 'true'})
        false_response = self.client.get(reverse('character-list'), {'is_demigod': 'false'})

        self.assertEqual(true_response.status_code, 200)
        self.assertEqual(
            [item['name'] for item in true_response.data['data']],
            ['Percy Jackson'],
        )
        self.assertEqual(false_response.status_code, 200)
        self.assertEqual([item['name'] for item in false_response.data['data']], ['Tyson'])

    def test_omitted_boolean_filter_does_not_filter_results(self):
        response = self.client.get(reverse('character-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['meta']['total'], 2)

    def test_noncanonical_boolean_values_return_bad_request(self):
        for value in ('True', 'FALSE', '1', '0', 'yes', 'no', 'maybe', ''):
            with self.subTest(value=value):
                response = self.client.get(
                    reverse('character-list'),
                    {'is_demigod': value},
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.data['error']['code'], 'BAD_REQUEST')

    def test_repeated_boolean_filter_values_return_bad_request(self):
        response = self.client.get(
            reverse('character-list'),
            {'is_demigod': ['true', 'false']},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error']['code'], 'BAD_REQUEST')
