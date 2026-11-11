from django.test import TestCase

from apps.organizations.serializers import (
    CabinDetailSerializer,
    CabinListSerializer,
    FactionDetailSerializer,
    FactionListSerializer,
    FactionMemberSerializer,
)
from tests.makers import (
    make_cabin,
    make_character,
    make_faction,
    make_god,
    make_monster,
    make_titan,
)


class CabinSerializerTests(TestCase):
    def setUp(self):
        self.god = make_god(name='Poseidon')
        self.cabin = make_cabin(number=3, deity=self.god)

    def test_list_serializer_includes_expected_fields(self):
        data = CabinListSerializer(self.cabin).data
        for field in ('slug', 'number', 'deity_slug', 'deity_name', 'is_honorary', 'is_empty'):
            self.assertIn(field, data)

    def test_list_serializer_deity_values(self):
        data = CabinListSerializer(self.cabin).data
        self.assertEqual(data['deity_slug'], 'poseidon')
        self.assertEqual(data['deity_name'], 'Poseidon')

    def test_list_serializer_handles_null_deity(self):
        honorary = make_cabin(number=2, deity=None, is_honorary=True)
        data = CabinListSerializer(honorary).data
        self.assertIsNone(data['deity_slug'])
        self.assertIsNone(data['deity_name'])

    def test_detail_serializer_known_camper_slugs(self):
        character = make_character(name='Percy Jackson')
        self.cabin.known_campers.add(character)
        data = CabinDetailSerializer(self.cabin).data
        self.assertIn('percy-jackson', data['known_camper_slugs'])

    def test_detail_serializer_handles_missing_counselor(self):
        data = CabinDetailSerializer(self.cabin).data
        self.assertIsNone(data['head_counselor_slug'])


class FactionSerializerTests(TestCase):
    def setUp(self):
        self.god = make_god(name='Artemis')
        self.faction = make_faction(name='Hunters of Artemis', leader_god=self.god)

    def test_list_serializer_flattens_god_leader(self):
        data = FactionListSerializer(self.faction).data
        self.assertEqual(data['leader']['type'], 'god')
        self.assertEqual(data['leader']['slug'], 'artemis')

    def test_list_serializer_handles_missing_leader(self):
        faction = make_faction(name='Leaderless')
        self.assertIsNone(FactionListSerializer(faction).data['leader'])

    def test_detail_serializer_member_slugs_and_typed_members(self):
        member = make_character(name='Zoe Nightshade')
        self.faction.members.add(member)
        data = FactionDetailSerializer(self.faction).data
        self.assertIn('zoe-nightshade', data['member_slugs'])
        self.assertIn(
            {'type': 'character', 'slug': 'zoe-nightshade', 'name': 'Zoe Nightshade'},
            data['members'],
        )

    def test_typed_member_serializer_supports_each_entity_type(self):
        entries = (
            ('character', make_character(name='Zoe Nightshade')),
            ('god', self.god),
            ('titan', make_titan(name='Atlas')),
            ('monster', make_monster(name='Alecto')),
        )
        serialized = []
        for member_type, entity in entries:
            field = f'member_{member_type}'
            membership = self.faction.member_records.create(**{field: entity})
            serialized.append(FactionMemberSerializer(membership).data)
        self.assertEqual([row['type'] for row in serialized], [kind for kind, _ in entries])

    def test_detail_serializer_flattens_character_leader(self):
        character = make_character(name='Chiron')
        faction = make_faction(name='Centaur Council', leader_character=character)
        data = FactionDetailSerializer(faction).data
        self.assertEqual(data['leader']['type'], 'character')
        self.assertEqual(data['leader']['name'], 'Chiron')
