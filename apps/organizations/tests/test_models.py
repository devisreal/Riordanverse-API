from django.db import IntegrityError, transaction
from django.test import TestCase

from tests.factories import make_cabin, make_character, make_faction, make_god


class CabinModelTests(TestCase):
    def setUp(self):
        self.god = make_god(name='Poseidon')
        self.cabin = make_cabin(number=3, deity=self.god)

    def test_string_representation(self):
        self.assertEqual(str(self.cabin), 'Cabin 3 — Poseidon')

    def test_slug_includes_deity(self):
        self.assertEqual(self.cabin.slug, 'cabin-3-poseidon')

    def test_slug_falls_back_to_number_without_deity(self):
        cabin = make_cabin(number=2, deity=None, is_honorary=True)
        self.assertEqual(cabin.slug, 'cabin-2')

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

    def test_members_many_to_many(self):
        faction = make_faction()
        member = make_character(name='Annabeth Chase')
        faction.members.add(member)
        self.assertIn(member, faction.members.all())
