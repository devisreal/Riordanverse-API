from django.urls import reverse

from apps.bestiary.models import CreatureMember, MonsterDefeat
from apps.core.tests.base import BaseAPITestCase
from tests.makers import make_book, make_character, make_creature, make_god, make_monster


class MonsterListViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.monster = make_monster(
            name='Medusa',
            monster_type='gorgon',
            allegiance='independent',
        )

    def test_list_returns_200(self):
        response = self.client.get(reverse('monster-list'))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_200(self):
        response = self.client.get(reverse('monster-detail', kwargs={'slug': 'medusa'}))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_404_for_unknown(self):
        response = self.client.get(reverse('monster-detail', kwargs={'slug': 'nobody'}))
        self.assertEqual(response.status_code, 404)

    def test_filter_by_monster_type(self):
        make_monster(name='Cyclops', monster_type='cyclops')
        response = self.client.get(reverse('monster-list'), {'monster_type': 'gorgon'})
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_can_reform(self):
        make_monster(name='Minotaur', can_reform=False)
        response = self.client.get(reverse('monster-list'), {'can_reform': 'true'})
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_defeated_by(self):
        percy = make_character(name='Percy Jackson')
        MonsterDefeat.objects.create(monster=self.monster, defeated_by=percy)
        response = self.client.get(reverse('monster-list'), {'defeated_by': 'percy-jackson'})
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_defeat_book(self):
        percy = make_character(name='Percy Jackson')
        book = make_book(title='The Sea of Monsters', book_number=2)
        MonsterDefeat.objects.create(monster=self.monster, defeated_by=percy, book=book)
        MonsterDefeat.objects.create(
            monster=self.monster,
            defeated_by=percy,
            book=book,
            method='A separate decisive subdual',
        )
        response = self.client.get(reverse('monster-list'), {'defeated_in_book': book.slug})
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_defeated_by_god(self):
        zeus = make_god(name='Zeus')
        self.monster.defeated_by_gods.add(zeus)
        response = self.client.get(reverse('monster-list'), {'defeated_by_god': 'zeus'})
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_extended_monster_type(self):
        make_monster(name='Dragon', monster_type='dragon')
        response = self.client.get(reverse('monster-list'), {'monster_type': 'dragon'})
        self.assertEqual(len(response.data['data']), 1)

    def test_invalid_monster_type_returns_400(self):
        response = self.client.get(reverse('monster-list'), {'monster_type': 'not-a-type'})
        self.assertEqual(response.status_code, 400)


class CreatureListViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.creature = make_creature(name='Satyr', alignment='olympian')

    def test_list_returns_200(self):
        response = self.client.get(reverse('creature-list'))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_200(self):
        response = self.client.get(reverse('creature-detail', kwargs={'slug': 'satyr'}))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_typed_character_and_monster_members(self):
        grover = make_character(name='Grover Underwood')
        polyphemus = make_monster(name='Polyphemus', monster_type='cyclops')
        self.creature.notable_members.add(grover)
        CreatureMember.objects.create(creature=self.creature, member_monster=polyphemus)

        response = self.client.get(reverse('creature-detail', kwargs={'slug': 'satyr'}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['notable_members'][0]['type'], 'character')
        self.assertEqual(response.data['notable_members'][1]['type'], 'monster')
        self.assertEqual(response.data['notable_member_slugs'], ['grover-underwood'])

    def test_members_subresource(self):
        grover = make_character(name='Grover Underwood')
        self.creature.notable_members.add(grover)
        response = self.client.get(reverse('creature-member-list', kwargs={'slug': 'satyr'}))
        self.assertEqual(response.status_code, 200)
        slugs = [character['slug'] for character in response.data['data']]
        self.assertIn('grover-underwood', slugs)
