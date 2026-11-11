from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from tests.makers import (
    make_character,
    make_divine_relationship,
    make_god,
    make_power,
    make_quest,
    make_weapon,
)


class CharacterListViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.poseidon = make_god(name='Poseidon')
        self.character = make_character(
            name='Percy Jackson',
            character_type='demigod',
            status='alive',
            is_big_three_child=True,
        )
        make_divine_relationship(from_entity=self.poseidon, to_entity=self.character)

    def test_list_returns_200_and_paginated_envelope(self):
        response = self.client.get(reverse('character-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.data)
        self.assertIn('meta', response.data)

    def test_detail_returns_200(self):
        response = self.client.get(reverse('character-detail', kwargs={'slug': 'percy-jackson'}))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_404_for_unknown(self):
        response = self.client.get(reverse('character-detail', kwargs={'slug': 'no-one'}))
        self.assertEqual(response.status_code, 404)

    def test_filter_by_divine_parent(self):
        make_character(name='Annabeth Chase', character_type='demigod')
        response = self.client.get(reverse('character-list'), {'divine_parent': 'poseidon'})
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['slug'], 'percy-jackson')

    def test_filter_is_big_three_child(self):
        make_character(name='Annabeth Chase')
        response = self.client.get(reverse('character-list'), {'is_big_three_child': 'true'})
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_status(self):
        make_character(name='Bianca di Angelo', status='deceased')
        response = self.client.get(reverse('character-list'), {'status': 'alive'})
        self.assertEqual(len(response.data['data']), 1)

    def test_invalid_status_returns_400(self):
        response = self.client.get(reverse('character-list'), {'status': 'transcended'})
        self.assertEqual(response.status_code, 400)

    def test_powers_subresource_returns_only_character_powers_in_order(self):
        make_power(
            self.character,
            name='Hydrokinesis',
            source='divine_parent',
            type='offensive',
            display_order=2,
        )
        make_power(self.character, name='Swordsmanship', source='training', display_order=1)
        other_character = make_character(name='Annabeth Chase')
        make_power(other_character, name='Wisdom', source='divine_parent')

        response = self.client.get(
            reverse('character-power-list', kwargs={'slug': self.character.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.data)
        self.assertIn('meta', response.data)
        self.assertEqual(
            [power['name'] for power in response.data['data']],
            ['Swordsmanship', 'Hydrokinesis'],
        )
        self.assertEqual(response.data['data'][0]['source'], 'training')

    def test_powers_subresource_filters_by_source_type_and_passive(self):
        make_power(
            self.character,
            name='Hydrokinesis',
            source='divine_parent',
            type='offensive',
            is_passive=False,
        )
        make_power(
            self.character,
            name='Ocean Breathing',
            source='divine_parent',
            type='utility',
            is_passive=True,
        )
        make_power(
            self.character,
            name='Swordsmanship',
            source='training',
            type='offensive',
            is_passive=False,
        )

        response = self.client.get(
            reverse('character-power-list', kwargs={'slug': self.character.slug}),
            {'source': 'divine_parent', 'type': 'offensive', 'is_passive': 'false'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([power['name'] for power in response.data['data']], ['Hydrokinesis'])

    def test_powers_subresource_rejects_invalid_filters(self):
        url = reverse('character-power-list', kwargs={'slug': self.character.slug})

        self.assertEqual(self.client.get(url, {'source': 'inherited'}).status_code, 400)
        self.assertEqual(self.client.get(url, {'type': 'superpowered'}).status_code, 400)
        self.assertEqual(self.client.get(url, {'is_passive': 'True'}).status_code, 400)

    def test_powers_subresource_returns_404_for_unknown_character(self):
        response = self.client.get(reverse('character-power-list', kwargs={'slug': 'no-one'}))

        self.assertEqual(response.status_code, 404)

    def test_no_standalone_powers_route(self):
        response = self.client.get('/api/v1/powers/')

        self.assertEqual(response.status_code, 404)

    def test_weapons_subresource(self):
        riptide = make_weapon(name='Riptide')
        self.character.weapons.add(riptide)
        response = self.client.get(
            reverse('character-weapon-list', kwargs={'slug': 'percy-jackson'})
        )
        self.assertEqual(response.status_code, 200)
        slugs = [weapon['slug'] for weapon in response.data['data']]
        self.assertIn('riptide', slugs)

    def test_quests_subresource(self):
        quest = make_quest(title='Quest for the Lightning Bolt')
        quest.participants.add(self.character)
        response = self.client.get(
            reverse('character-quest-list', kwargs={'slug': 'percy-jackson'})
        )
        self.assertEqual(response.status_code, 200)
        slugs = [item['slug'] for item in response.data['data']]
        self.assertIn(quest.slug, slugs)
