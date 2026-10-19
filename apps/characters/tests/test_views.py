from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from tests.makers import make_character, make_god, make_quest, make_weapon


class CharacterListViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.poseidon = make_god(name='Poseidon')
        self.character = make_character(
            name='Percy Jackson',
            character_type='demigod',
            status='alive',
            divine_parent=self.poseidon,
            is_big_three_child=True,
        )

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
