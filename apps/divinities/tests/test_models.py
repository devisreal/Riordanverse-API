from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.divinities.models import DivineRelationship
from tests.makers import make_character, make_divine_relationship, make_god, make_titan


class GodModelTests(TestCase):
    def setUp(self):
        self.god = make_god(name='Poseidon', tier='olympian')

    def test_string_representation(self):
        self.assertEqual(str(self.god), 'Poseidon')

    def test_slug_generated(self):
        self.assertEqual(self.god.slug, 'poseidon')

    def test_domains_default_to_empty_list(self):
        self.assertEqual(self.god.domains, [])

    def test_domains_accept_a_list(self):
        self.god.domains = ['sea', 'earthquakes', 'horses']
        self.god.save()
        self.god.refresh_from_db()
        self.assertEqual(len(self.god.domains), 3)

    def test_children_demigods_many_to_many(self):
        percy = make_character(name='Percy Jackson')
        self.god.children_demigods.add(percy)
        self.assertIn(percy, self.god.children_demigods.all())


class TitanModelTests(TestCase):
    def setUp(self):
        self.titan = make_titan(name='Kronos')

    def test_string_representation(self):
        self.assertEqual(str(self.titan), 'Kronos')

    def test_slug_generated(self):
        self.assertEqual(self.titan.slug, 'kronos')

    def test_domains_default_to_empty_list(self):
        self.assertEqual(self.titan.domains, [])

    def test_sacred_attributes_default_to_empty_lists(self):
        self.assertEqual(self.titan.sacred_animals, [])
        self.assertEqual(self.titan.sacred_plants, [])

    def test_sacred_attributes_accept_lists(self):
        self.titan.sacred_animals = ['white horse']
        self.titan.sacred_plants = ['heliotrope']
        self.titan.save()
        self.titan.refresh_from_db()
        self.assertEqual(self.titan.sacred_animals, ['white horse'])
        self.assertEqual(self.titan.sacred_plants, ['heliotrope'])


class DivineRelationshipTests(TestCase):
    def setUp(self):
        self.zeus = make_god(name='Zeus')
        self.kronos = make_titan(name='Kronos')
        self.athena = make_god(name='Athena')

    def test_god_to_god_relationship(self):
        relationship = make_divine_relationship(
            from_entity=self.zeus,
            to_entity=self.athena,
            relationship_type='parent_of',
        )
        self.assertEqual(relationship.from_god, self.zeus)
        self.assertEqual(relationship.to_god, self.athena)
        self.assertIsNone(relationship.from_titan)
        self.assertIsNone(relationship.to_titan)

    def test_titan_to_god_relationship(self):
        relationship = make_divine_relationship(
            from_entity=self.kronos,
            to_entity=self.zeus,
            relationship_type='parent_of',
        )
        self.assertEqual(relationship.from_titan, self.kronos)
        self.assertEqual(relationship.to_god, self.zeus)
        self.assertIsNone(relationship.from_god)
        self.assertIsNone(relationship.to_titan)

    def test_string_representation(self):
        relationship = make_divine_relationship(
            from_entity=self.kronos,
            to_entity=self.zeus,
            relationship_type='parent_of',
        )
        self.assertIn('Kronos', str(relationship))
        self.assertIn('Zeus', str(relationship))

    def test_check_constraint_rejects_both_from_entities(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            DivineRelationship.objects.create(
                from_god=self.zeus,
                from_titan=self.kronos,
                to_god=self.athena,
                relationship_type='sibling_of',
            )

    def test_check_constraint_rejects_both_to_entities(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            DivineRelationship.objects.create(
                from_god=self.zeus,
                to_god=self.athena,
                to_titan=self.kronos,
                relationship_type='sibling_of',
            )

    def test_unique_relationship_constraint(self):
        make_divine_relationship(
            from_entity=self.kronos,
            to_entity=self.zeus,
            relationship_type='parent_of',
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_divine_relationship(
                from_entity=self.kronos,
                to_entity=self.zeus,
                relationship_type='parent_of',
            )
