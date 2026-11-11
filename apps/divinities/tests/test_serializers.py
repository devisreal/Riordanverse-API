from django.test import TestCase

from apps.bestiary.serializers import (
    CreatureDetailSerializer,
    CreatureListSerializer,
    MonsterDetailSerializer,
    MonsterListSerializer,
)
from apps.characters.serializers import CharacterDetailSerializer, CharacterListSerializer
from apps.divinities.serializers import (
    GodDetailSerializer,
    GodListSerializer,
    TitanDetailSerializer,
    TitanListSerializer,
)
from tests.makers import (
    make_character,
    make_creature,
    make_divine_relationship,
    make_god,
    make_monster,
    make_titan,
    make_weapon,
)


class FamilyDetailSerializerTests(TestCase):
    def test_family_is_detail_only(self):
        collections = (
            GodListSerializer(make_god(name='Zeus')).data,
            TitanListSerializer(make_titan(name='Kronos')).data,
            CharacterListSerializer(make_character(name='Percy Jackson')).data,
            MonsterListSerializer(make_monster(name='Medusa')).data,
            CreatureListSerializer(make_creature(name='Cyclops')).data,
        )
        for payload in collections:
            self.assertNotIn('type', payload)
            self.assertNotIn('family', payload)

    def test_all_detail_serializers_use_the_same_typed_family_envelope(self):
        entities = (
            ('god', GodDetailSerializer(make_god(name='Zeus')).data),
            ('titan', TitanDetailSerializer(make_titan(name='Kronos')).data),
            ('character', CharacterDetailSerializer(make_character(name='Percy Jackson')).data),
            ('monster', MonsterDetailSerializer(make_monster(name='Medusa')).data),
            ('creature', CreatureDetailSerializer(make_creature(name='Cyclops')).data),
        )
        for entity_type, payload in entities:
            with self.subTest(entity_type=entity_type):
                self.assertEqual(payload['type'], entity_type)
                self.assertEqual(
                    set(payload['family']), {'parents', 'siblings', 'consorts', 'children'}
                )
                self.assertTrue(all(value == [] for value in payload['family'].values()))

    def test_god_detail_has_nested_typed_parents_and_no_top_level_relationship_lists(self):
        kronos = make_titan(name='Kronos')
        zeus = make_god(name='Zeus', tier='olympian')
        make_divine_relationship(from_entity=kronos, to_entity=zeus)

        data = GodDetailSerializer(zeus).data
        self.assertEqual(data['type'], 'god')
        self.assertEqual(
            data['family']['parents'],
            [{'name': 'Kronos', 'type': 'titan', 'slug': 'kronos'}],
        )
        self.assertEqual(data['family']['siblings'], [])
        for old_field in ('parents', 'siblings', 'consorts', 'children', 'children_demigod_slugs'):
            self.assertNotIn(old_field, data)

    def test_character_parent_and_sibling_relations_are_nested(self):
        poseidon = make_god(name='Poseidon')
        percy = make_character(name='Percy Jackson')
        tyson = make_character(name='Tyson', character_type='cyclops', species='cyclops')
        make_divine_relationship(from_entity=poseidon, to_entity=percy)
        make_divine_relationship(from_entity=percy, to_entity=tyson, relationship_type='sibling_of')

        data = __import__('apps.characters.serializers', fromlist=['CharacterDetailSerializer'])
        detail = data.CharacterDetailSerializer(percy).data
        self.assertEqual(detail['type'], 'character')
        self.assertEqual(detail['family']['parents'][0]['type'], 'god')
        self.assertEqual(detail['family']['siblings'][0]['slug'], 'tyson')
        for old_field in ('divine_parent_slug', 'mortal_parent_ref_slug', 'sibling_slugs'):
            self.assertNotIn(old_field, detail)

    def test_family_relationships_are_visible_from_both_sides(self):
        apollo = make_god(name='Apollo')
        artemis = make_god(name='Artemis')
        make_divine_relationship(
            from_entity=apollo, to_entity=artemis, relationship_type='sibling_of'
        )

        self.assertEqual(
            GodDetailSerializer(apollo).data['family']['siblings'][0]['slug'], 'artemis'
        )
        self.assertEqual(
            GodDetailSerializer(artemis).data['family']['siblings'][0]['slug'], 'apollo'
        )

    def test_children_and_legacy_child_of_are_normalized_in_response(self):
        rhea = make_titan(name='Rhea')
        kronos = make_titan(name='Kronos')
        zeus = make_god(name='Zeus')
        make_divine_relationship(from_entity=rhea, to_entity=kronos, relationship_type='child_of')
        make_divine_relationship(from_entity=kronos, to_entity=zeus)

        self.assertEqual(TitanDetailSerializer(rhea).data['family']['parents'][0]['slug'], 'kronos')
        child_slugs = {
            item['slug'] for item in TitanDetailSerializer(kronos).data['family']['children']
        }
        self.assertSetEqual(child_slugs, {'rhea', 'zeus'})

    def test_god_consort_relationship_is_visible_from_both_entities(self):
        hera = make_god(name='Hera')
        zeus = make_god(name='Zeus')
        make_divine_relationship(from_entity=hera, to_entity=zeus, relationship_type='consort_of')

        self.assertEqual(GodDetailSerializer(hera).data['family']['consorts'][0]['slug'], 'zeus')
        self.assertEqual(GodDetailSerializer(zeus).data['family']['consorts'][0]['slug'], 'hera')

    def test_titan_children_include_characters(self):
        kronos = make_titan(name='Kronos')
        phaethon = make_character(name='Phaethon')
        make_divine_relationship(from_entity=kronos, to_entity=phaethon)

        data = TitanDetailSerializer(kronos).data
        self.assertEqual(data['type'], 'titan')
        self.assertEqual(data['family']['children'][0]['type'], 'character')

    def test_monster_family_can_reference_characters_and_creatures(self):
        minotaur = make_monster(name='The Minotaur', slug='minotaur')
        pasiphae = make_character(name='Pasiphaë', slug='pasiphae')
        bull = make_creature(name='Cretan Bull', slug='cretan-bull')
        ariadne = make_character(name='Ariadne', slug='ariadne')
        make_divine_relationship(from_entity=pasiphae, to_entity=minotaur)
        make_divine_relationship(from_entity=bull, to_entity=minotaur)
        make_divine_relationship(
            from_entity=minotaur, to_entity=ariadne, relationship_type='sibling_of'
        )

        data = MonsterDetailSerializer(minotaur).data
        self.assertEqual(data['type'], 'monster')
        self.assertEqual(
            {(ref['type'], ref['slug']) for ref in data['family']['parents']},
            {('character', 'pasiphae'), ('creature', 'cretan-bull')},
        )
        self.assertEqual(data['family']['siblings'][0]['slug'], 'ariadne')
        self.assertNotIn('parent_entity', data)

    def test_creature_can_have_monster_and_god_family_links(self):
        bull = make_creature(name='Cretan Bull')
        poseidon = make_god(name='Poseidon')
        minotaur = make_monster(name='The Minotaur')
        make_divine_relationship(from_entity=poseidon, to_entity=bull)
        make_divine_relationship(from_entity=bull, to_entity=minotaur)

        data = CreatureDetailSerializer(bull).data
        self.assertEqual(data['type'], 'creature')
        self.assertEqual(data['family']['parents'][0]['type'], 'god')
        self.assertEqual(data['family']['children'][0]['type'], 'monster')

    def test_titan_weapon_and_non_family_fields_remain(self):
        kronos = make_titan(name='Kronos')
        weapon = make_weapon(name='Kronos Scythe')
        kronos.weapons.add(weapon)
        kronos.home = 'Mount Othrys'
        kronos.sacred_animals = ['white horse']
        kronos.save()

        data = TitanDetailSerializer(kronos).data
        self.assertEqual(data['weapon_slugs'], ['kronos-scythe'])
        self.assertEqual(data['home'], 'Mount Othrys')
        self.assertEqual(data['sacred_animals'], ['white horse'])
