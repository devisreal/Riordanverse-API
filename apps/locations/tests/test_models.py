from django.db import IntegrityError, transaction
from django.test import TestCase

from tests.makers import make_character, make_god, make_location, make_titan


class LocationModelTests(TestCase):
    def setUp(self):
        self.location = make_location(name='Camp Half-Blood', location_type='camp')

    def test_string_representation(self):
        self.assertEqual(str(self.location), 'Camp Half-Blood')

    def test_slug_generated(self):
        self.assertEqual(self.location.slug, 'camp-half-blood')

    def test_notable_events_default_to_empty_list(self):
        self.assertEqual(self.location.notable_events, [])

    def test_is_hidden_from_mortals_defaults_false(self):
        self.assertFalse(self.location.is_hidden_from_mortals)

    def test_controlled_by_god(self):
        hades = make_god(name='Hades')
        self.location.controlled_by_god = hades
        self.location.save()
        self.assertEqual(self.location.controlled_by_god, hades)
        self.assertIsNone(self.location.controlled_by_titan)
        self.assertIsNone(self.location.controlled_by_character)

    def test_constraint_rejects_god_and_titan(self):
        hades = make_god(name='Hades')
        kronos = make_titan(name='Kronos')
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_location(
                name='Contested Land',
                controlled_by_god=hades,
                controlled_by_titan=kronos,
            )

    def test_constraint_rejects_god_and_character(self):
        hades = make_god(name='Hades')
        luke = make_character(name='Luke Castellan')
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_location(
                name='Contested Land',
                controlled_by_god=hades,
                controlled_by_character=luke,
            )

    def test_constraint_rejects_titan_and_character(self):
        kronos = make_titan(name='Kronos')
        luke = make_character(name='Luke Castellan')
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_location(
                name='Contested Land',
                controlled_by_titan=kronos,
                controlled_by_character=luke,
            )

    def test_all_controllers_null_is_valid(self):
        location = make_location(name='Wild Forest')
        self.assertIsNone(location.controlled_by_god)
        self.assertIsNone(location.controlled_by_titan)
        self.assertIsNone(location.controlled_by_character)
