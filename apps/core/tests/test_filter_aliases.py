from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from tests.makers import (
    make_book,
    make_character,
    make_event,
    make_location,
    make_monster,
    make_weapon,
)


class DocumentedFilterAliasTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        make_book(title='The Lightning Thief', book_type='novel')
        make_character(
            name='Thalia Grace',
            character_type='demigod',
            affiliation=['hunters_of_artemis'],
        )
        make_event(name='Battle of Manhattan', event_type='battle')
        make_location(name='New York City', location_type='mortal_city')
        make_monster(name='Chimera', monster_type='chimeric')
        make_weapon(name='Riptide', weapon_type='sword')

    def test_type_aliases_work_alongside_model_specific_filter_names(self):
        cases = (
            ('book-list', 'novel'),
            ('character-list', 'demigod'),
            ('event-list', 'battle'),
            ('location-list', 'mortal_city'),
            ('monster-list', 'chimeric'),
            ('weapon-list', 'sword'),
        )
        for route_name, value in cases:
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name), {'type': value})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data['meta']['total'], 1)

    def test_character_affiliation_filter_checks_membership_in_json_array(self):
        response = self.client.get(
            reverse('character-list'),
            {'affiliation': 'hunters_of_artemis'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [character['name'] for character in response.data['data']],
            ['Thalia Grace'],
        )

    def test_type_aliases_keep_strict_choice_validation(self):
        response = self.client.get(reverse('character-list'), {'type': 'Demigod'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error']['code'], 'BAD_REQUEST')
