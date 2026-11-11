from django.db import IntegrityError, transaction
from django.test import TestCase

from tests.makers import make_character, make_god, make_titan, make_weapon


class WeaponModelTests(TestCase):
    def setUp(self):
        self.weapon = make_weapon(name='Riptide', weapon_type='sword')

    def test_string_representation(self):
        self.assertEqual(str(self.weapon), 'Riptide')

    def test_slug_generated(self):
        self.assertEqual(self.weapon.slug, 'riptide')

    def test_form_defaults_to_empty_list(self):
        self.assertEqual(self.weapon.form, [])

    def test_abilities_default_to_empty_list(self):
        self.assertEqual(self.weapon.abilities, [])

    def test_owner_history_defaults_to_empty_list(self):
        self.assertEqual(self.weapon.owner_history, [])

    def test_character_owner_only(self):
        percy = make_character(name='Percy Jackson')
        self.weapon.owner_primary_character = percy
        self.weapon.save()
        self.assertEqual(self.weapon.owner_primary_character, percy)
        self.assertIsNone(self.weapon.owner_primary_god)

    def test_god_owner_only(self):
        poseidon = make_god(name='Poseidon')
        self.weapon.owner_primary_god = poseidon
        self.weapon.save()
        self.assertEqual(self.weapon.owner_primary_god, poseidon)
        self.assertIsNone(self.weapon.owner_primary_character)
        self.assertIsNone(self.weapon.owner_primary_titan)

    def test_titan_owner_only(self):
        kronos = make_titan(name='Kronos')
        self.weapon.owner_primary_titan = kronos
        self.weapon.save()
        self.assertEqual(self.weapon.owner_primary_titan, kronos)
        self.assertIsNone(self.weapon.owner_primary_character)
        self.assertIsNone(self.weapon.owner_primary_god)

    def test_check_constraint_rejects_both_owners(self):
        percy = make_character(name='Percy Jackson')
        poseidon = make_god(name='Poseidon')
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_weapon(
                name='Dual Weapon',
                owner_primary_character=percy,
                owner_primary_god=poseidon,
            )

    def test_check_constraint_rejects_character_and_titan_owners(self):
        percy = make_character(name='Percy Jackson')
        kronos = make_titan(name='Kronos')
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_weapon(
                name='Dual Owner Weapon',
                owner_primary_character=percy,
                owner_primary_titan=kronos,
            )

    def test_both_owners_null_is_valid(self):
        unclaimed = make_weapon(name='Unclaimed Artifact')
        self.assertIsNone(unclaimed.owner_primary_character)
        self.assertIsNone(unclaimed.owner_primary_god)
        self.assertIsNone(unclaimed.owner_primary_titan)

    def test_forged_by_character_only(self):
        tyson = make_character(name='Tyson')
        self.weapon.forged_by_character = tyson
        self.weapon.save()
        self.assertEqual(self.weapon.forged_by_character, tyson)
        self.assertIsNone(self.weapon.forged_by)

    def test_forged_by_constraints_reject_god_and_character(self):
        hephaestus = make_god(name='Hephaestus')
        daedalus = make_character(name='Daedalus')
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_weapon(
                name='Dually Forged',
                forged_by=hephaestus,
                forged_by_character=daedalus,
            )

    def test_true_name_is_optional(self):
        weapon = make_weapon(name='Sword', true_name='Anaklusmos')
        self.assertEqual(weapon.true_name, 'Anaklusmos')
