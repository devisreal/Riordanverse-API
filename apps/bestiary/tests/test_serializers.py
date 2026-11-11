from django.test import TestCase

from apps.bestiary.models import CreatureMember, MonsterDefeat
from apps.bestiary.serializers import CreatureDetailSerializer, MonsterDetailSerializer
from tests.makers import make_book, make_character, make_god, make_monster


class CreatureDetailSerializerTests(TestCase):
    def test_returns_typed_members_and_legacy_character_slugs(self):
        from tests.makers import make_creature

        creature = make_creature(name='Cyclops')
        tyson = make_character(name='Tyson')
        polyphemus = make_monster(name='Polyphemus', monster_type='cyclops')
        creature.notable_members.add(tyson)
        CreatureMember.objects.create(creature=creature, member_monster=polyphemus)

        data = CreatureDetailSerializer(creature).data

        self.assertEqual(
            data['notable_members'],
            [
                {'type': 'character', 'slug': 'tyson', 'name': 'Tyson'},
                {'type': 'monster', 'slug': 'polyphemus', 'name': 'Polyphemus'},
            ],
        )
        self.assertEqual(data['notable_member_slugs'], ['tyson'])


class MonsterDetailSerializerTests(TestCase):
    def setUp(self):
        self.monster = make_monster(name='Medusa', monster_type='gorgon')

    def test_defeated_by_slugs_empty(self):
        data = MonsterDetailSerializer(self.monster).data
        self.assertEqual(data['defeated_by_slugs'], [])

    def test_defeated_by_slugs_populated(self):
        percy = make_character(name='Percy Jackson')
        MonsterDefeat.objects.create(monster=self.monster, defeated_by=percy)
        data = MonsterDetailSerializer(self.monster).data
        self.assertIn('percy-jackson', data['defeated_by_slugs'])

    def test_defeats_are_serialized_as_events(self):
        percy = make_character(name='Percy Jackson')
        book = make_book(title='The Sea of Monsters', book_number=2)
        MonsterDefeat.objects.create(
            monster=self.monster,
            defeated_by=percy,
            book=book,
            method='Tricked and subdued',
            is_myth=False,
        )
        data = MonsterDetailSerializer(self.monster).data
        self.assertEqual(
            data['defeats'],
            [
                {
                    'defeated_by': 'percy-jackson',
                    'book': book.slug,
                    'method': 'Tricked and subdued',
                    'is_myth': False,
                }
            ],
        )

    def test_defeated_by_god_slugs_populated(self):
        zeus = make_god(name='Zeus')
        self.monster.defeated_by_gods.add(zeus)
        data = MonsterDetailSerializer(self.monster).data
        self.assertEqual(data['defeated_by_god_slugs'], ['zeus'])

    def test_monster_type_display(self):
        data = MonsterDetailSerializer(self.monster).data
        self.assertEqual(data['monster_type_display'], 'Gorgon')

    def test_aliases_field(self):
        self.monster.aliases = ['Aunty Em']
        self.monster.save()
        data = MonsterDetailSerializer(self.monster).data
        self.assertIn('Aunty Em', data['aliases'])
