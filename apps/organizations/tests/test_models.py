from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.organizations.models import FactionMember
from tests.makers import (
    make_cabin,
    make_character,
    make_faction,
    make_god,
    make_monster,
    make_titan,
)


class CabinModelTests(TestCase):
    def setUp(self):
        self.god = make_god(name='Poseidon')
        self.cabin = make_cabin(number=3, deity=self.god)

    def test_string_representation(self):
        self.assertEqual(str(self.cabin), 'Cabin 3 — Poseidon')

    def test_slug_includes_deity(self):
        self.assertEqual(self.cabin.slug, 'cabin-3-poseidon')

    def test_honorary_cabin_slug_uses_canonical_deity_name(self):
        cabin = make_cabin(number=2, deity=None, is_honorary=True)
        self.assertEqual(cabin.slug, 'cabin-2-hera')

    def test_artemis_honorary_cabin_slug_is_canonical(self):
        cabin = make_cabin(number=8, deity=None, is_honorary=True)
        self.assertEqual(cabin.slug, 'cabin-8-artemis')

    def test_cabin_number_is_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_cabin(number=3)

    def test_deity_is_optional(self):
        cabin = make_cabin(number=8, deity=None, is_honorary=True)
        self.assertIsNone(cabin.deity)

    def test_god_reverse_accessor_is_cabin(self):
        self.assertEqual(self.god.cabin, self.cabin)

    def test_known_campers_many_to_many(self):
        character = make_character(name='Percy Jackson')
        self.cabin.known_campers.add(character)
        self.assertIn(character, self.cabin.known_campers.all())


class FactionModelTests(TestCase):
    def setUp(self):
        self.character = make_character(name='Chiron')
        self.god = make_god(name='Artemis')

    def test_string_representation(self):
        faction = make_faction(name='Camp Half-Blood')
        self.assertEqual(str(faction), 'Camp Half-Blood')

    def test_slug_generated_from_name(self):
        faction = make_faction(name='Hunters of Artemis')
        self.assertEqual(faction.slug, 'hunters-of-artemis')

    def test_both_leaders_null_is_valid(self):
        faction = make_faction()
        self.assertIsNone(faction.leader_character)
        self.assertIsNone(faction.leader_god)

    def test_character_leader_only_is_valid(self):
        faction = make_faction(leader_character=self.character)
        self.assertEqual(faction.leader_character, self.character)
        self.assertIsNone(faction.leader_god)

    def test_god_leader_only_is_valid(self):
        faction = make_faction(leader_god=self.god)
        self.assertEqual(faction.leader_god, self.god)
        self.assertIsNone(faction.leader_character)

    def test_both_leaders_violate_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_faction(leader_character=self.character, leader_god=self.god)

    def test_character_members_many_to_many(self):
        faction = make_faction()
        member = make_character(name='Annabeth Chase')
        faction.members.add(member)
        self.assertIn(member, faction.members.all())
        self.assertEqual(faction.member_records.get().member_character, member)

    def test_typed_member_links_support_all_entity_types(self):
        faction = make_faction()
        character = make_character(name='Annabeth Chase')
        god = make_god(name='Athena')
        titan = make_titan(name='Atlas')
        monster = make_monster(name='Alecto')

        for field, entity in (
            ('member_character', character),
            ('member_god', god),
            ('member_titan', titan),
            ('member_monster', monster),
        ):
            FactionMember.objects.create(faction=faction, **{field: entity})

        self.assertEqual(faction.member_records.count(), 4)

    def test_member_requires_exactly_one_entity(self):
        faction = make_faction()
        with self.assertRaises(IntegrityError), transaction.atomic():
            FactionMember.objects.create(faction=faction)

    def test_member_rejects_multiple_entity_types(self):
        faction = make_faction()
        with self.assertRaises(IntegrityError), transaction.atomic():
            FactionMember.objects.create(
                faction=faction,
                member_character=make_character(),
                member_god=make_god(),
            )
