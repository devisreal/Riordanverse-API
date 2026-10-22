import watson.search as watson
from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from apps.search.adapters import ADAPTERS, CabinSearchAdapter
from tests.makers import (
    make_cabin,
    make_character,
    make_god,
    make_monster,
    make_weapon,
)


class SearchViewTests(BaseAPITestCase):
    def test_all_thirteen_lore_models_are_registered(self):
        self.assertEqual(len(ADAPTERS), 13)
        self.assertEqual(len(watson.get_registered_models()), 13)

    def test_cabin_index_queryset_selects_deity(self):
        from apps.organizations.models import Cabin

        queryset = CabinSearchAdapter(Cabin).get_live_queryset()
        self.assertIn('deity', queryset.query.select_related)

    def setUp(self):
        super().setUp()
        with watson.update_index():
            self.percy = make_character(
                name='Percy Jackson',
                aliases=['Seaweed Brain'],
                description='Hero of Olympus and son of Poseidon.',
                wiki_url='https://riordan.fandom.com/wiki/Percy_Jackson',
            )
            self.riptide = make_weapon(
                name='Riptide',
                true_name='Anaklusmos',
                abilities=['always returns to its owner'],
                description="Percy's Celestial Bronze sword.",
            )
            self.medusa = make_monster(
                name='Medusa',
                aliases=['Aunty Em'],
                description='A Gorgon who turns victims to stone.',
            )
            self.poseidon = make_god(
                name='Poseidon',
                domains=['sea', 'earthquakes'],
                description='God of the sea.',
            )
            self.poseidon_cabin = make_cabin(
                number=3,
                deity=self.poseidon,
                architecture_description='A blue cabin by the shore.',
            )

    def search(self, query, **params):
        return self.client.get(reverse('search'), {'q': query, **params})

    def test_missing_q_returns_400(self):
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error']['code'], 'BAD_REQUEST')

    def test_blank_q_returns_400(self):
        response = self.search('  ')
        self.assertEqual(response.status_code, 400)

    def test_search_returns_data_and_meta_envelope(self):
        response = self.search('Percy')
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.data)
        self.assertIn('meta', response.data)
        self.assertEqual(response.data['meta']['query'], 'Percy')
        self.assertIsNone(response.data['meta']['type_filter'])

    def test_result_includes_type_slug_url_title_and_description(self):
        response = self.search('Percy')
        result = next(item for item in response.data['data'] if item['slug'] == 'percy-jackson')
        self.assertEqual(result['type'], 'character')
        self.assertEqual(result['url'], '/api/v1/characters/percy-jackson/')
        self.assertEqual(result['title'], 'Percy Jackson')
        self.assertEqual(result['description'], 'Hero of Olympus and son of Poseidon.')
        self.assertEqual(result['wiki_url'], 'https://riordan.fandom.com/wiki/Percy_Jackson')

    def test_search_indexes_character_aliases(self):
        response = self.search('Seaweed Brain')
        self.assertIn('percy-jackson', [result['slug'] for result in response.data['data']])

    def test_search_indexes_monster_aliases(self):
        response = self.search('Aunty Em')
        self.assertIn('medusa', [result['slug'] for result in response.data['data']])

    def test_search_indexes_weapon_true_name(self):
        response = self.search('Anaklusmos')
        self.assertIn('riptide', [result['slug'] for result in response.data['data']])

    def test_search_indexes_god_domains(self):
        response = self.search('earthquakes')
        self.assertIn('poseidon', [result['slug'] for result in response.data['data']])

    def test_type_filter_returns_only_matching_model(self):
        response = self.search('Poseidon', type='god')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['meta']['type_filter'], 'god')
        self.assertEqual([result['type'] for result in response.data['data']], ['god'])

    def test_invalid_type_returns_400_and_lists_valid_options(self):
        response = self.search('Percy', type='wizard')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error']['code'], 'BAD_REQUEST')
        self.assertIn('character', response.data['error']['message'])

    def test_search_is_case_insensitive(self):
        response = self.search('rIpTiDe')
        self.assertIn('riptide', [result['slug'] for result in response.data['data']])

    def test_cabin_search_result_has_custom_title(self):
        response = self.search('Cabin 3 Poseidon', type='cabin')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data'][0]['title'], 'Cabin 3 — Poseidon')
