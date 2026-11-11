from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.bestiary.models import CreatureMember, MonsterDefeat
from tests.makers import make_book, make_character, make_creature, make_god, make_monster


class MonsterModelTests(TestCase):
    def setUp(self):
        self.monster = make_monster(
            name='Medusa',
            monster_type='gorgon',
            allegiance='independent',
        )

    def test_string_representation(self):
        self.assertEqual(str(self.monster), 'Medusa')

    def test_slug_generated(self):
        self.assertEqual(self.monster.slug, 'medusa')

    def test_aliases_default_to_empty_list(self):
        self.assertEqual(self.monster.aliases, [])

    def test_aliases_accept_a_list(self):
        self.monster.aliases = ['Aunty Em']
        self.monster.save()
        self.monster.refresh_from_db()
        self.assertEqual(self.monster.aliases, ['Aunty Em'])

    def test_can_reform_defaults_true(self):
        self.assertTrue(self.monster.can_reform)

    def test_defeated_by_many_to_many_reverse_relation(self):
        percy = make_character(name='Percy Jackson')
        defeat = MonsterDefeat.objects.create(monster=self.monster, defeated_by=percy)
        self.assertIn(percy, self.monster.defeated_by.all())
        self.assertIn(defeat, percy.monsters_defeated.all())

    def test_defeat_event_records_book_method_and_myth_flag(self):
        percy = make_character(name='Percy Jackson')
        book = make_book(title='The Sea of Monsters', book_number=2)
        defeat = MonsterDefeat.objects.create(
            monster=self.monster,
            defeated_by=percy,
            book=book,
            method='Tricked and subdued in single combat',
            is_myth=False,
        )
        self.assertEqual(self.monster.defeats.get(), defeat)
        self.assertEqual(defeat.book, book)
        self.assertEqual(defeat.method, 'Tricked and subdued in single combat')
        self.assertFalse(defeat.is_myth)
        self.assertIn(defeat, percy.monsters_defeated.all())

    def test_mythic_defeat_can_have_no_book(self):
        heracles = make_character(name='Heracles')
        defeat = MonsterDefeat.objects.create(
            monster=self.monster,
            defeated_by=heracles,
            is_myth=True,
        )
        self.assertIsNone(defeat.book)
        self.assertTrue(defeat.is_myth)

    def test_defeated_by_gods_many_to_many_reverse_relation(self):
        zeus = make_god(name='Zeus')
        self.monster.defeated_by_gods.add(zeus)
        self.assertIn(zeus, self.monster.defeated_by_gods.all())
        self.assertIn(self.monster, zeus.monsters_defeated.all())

    def test_extended_monster_type_persists(self):
        self.monster.monster_type = 'ancient_dragon_jailer'
        self.monster.save()
        self.monster.refresh_from_db()
        self.assertEqual(self.monster.monster_type, 'ancient_dragon_jailer')


class CreatureModelTests(TestCase):
    def setUp(self):
        self.creature = make_creature(name='Satyr', alignment='olympian')

    def test_string_representation(self):
        self.assertEqual(str(self.creature), 'Satyr')

    def test_slug_generated(self):
        self.assertEqual(self.creature.slug, 'satyr')

    def test_notable_members_many_to_many(self):
        grover = make_character(name='Grover Underwood')
        self.creature.notable_members.add(grover)
        self.assertIn(grover, self.creature.notable_members.all())

    def test_member_records_support_character_and_monster_and_preserve_legacy_m2m(self):
        grover = make_character(name='Grover Underwood')
        polyphemus = make_monster(name='Polyphemus', monster_type='cyclops')
        self.creature.notable_members.add(grover)
        CreatureMember.objects.create(creature=self.creature, member_monster=polyphemus)

        self.assertEqual(self.creature.member_records.count(), 2)
        self.assertIn(grover, self.creature.notable_members.all())
        self.assertNotIn(polyphemus, self.creature.notable_members.all())

    def test_member_record_requires_exactly_one_entity(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CreatureMember.objects.create(creature=self.creature)

    def test_member_record_rejects_multiple_entity_types(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CreatureMember.objects.create(
                creature=self.creature,
                member_character=make_character(name='Grover Underwood'),
                member_monster=make_monster(name='Polyphemus', monster_type='cyclops'),
            )
