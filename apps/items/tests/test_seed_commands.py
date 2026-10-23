from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.characters.models import Character
from apps.divinities.models import God, Titan
from apps.items.models import Weapon


class WeaponSeedCommandTests(TestCase):
    def test_seed_weapons_resolves_relationships_and_is_idempotent(self):
        bow = Weapon.objects.create(
            name='Bow of Heracles', wiki_url='https://riordan.fandom.com/wiki/Verified_Bow'
        )
        outputs = []
        for command in (
            'seed_books',
            'seed_gods',
            'seed_titans',
            'seed_characters',
            'seed_items',
        ):
            output = StringIO()
            call_command(command, stdout=output)
            outputs.append(output.getvalue())

        self.assertEqual(Weapon.objects.count(), 40)
        self.assertEqual(Weapon.objects.filter(wiki_url__isnull=False).count(), 35)
        self.assertEqual(
            Weapon.objects.get(slug='riptide').wiki_url,
            'https://riordan.fandom.com/wiki/Riptide',
        )
        bow.refresh_from_db()
        self.assertEqual(bow.wiki_url, 'https://riordan.fandom.com/wiki/Verified_Bow')
        self.assertFalse(any('[WARN]' in output for output in outputs))

        kronos = Titan.objects.get(slug='kronos')
        kronos_scythe = Weapon.objects.get(slug='kronos-scythe')
        adamantine_scythe = Weapon.objects.get(slug='adamantine-scythe')
        self.assertEqual(kronos_scythe.owner_primary_titan, kronos)
        self.assertEqual(adamantine_scythe.owner_primary_titan, kronos)
        self.assertEqual(adamantine_scythe.material, 'flint')

        daedalus = Character.objects.get(slug='daedalus')
        tyson = Character.objects.get(slug='tyson')
        ariadnes_string = Weapon.objects.get(slug='ariadnes-string')
        tysons_shield = Weapon.objects.get(slug='tysons-shield')
        self.assertEqual(ariadnes_string.forged_by_character, daedalus)
        self.assertEqual(tysons_shield.forged_by_character, tyson)

        golden_celedon = Weapon.objects.get(slug='golden-celedon')
        apollo = God.objects.get(slug='apollo')
        self.assertEqual(golden_celedon.owner_primary_god, apollo)
        self.assertEqual(golden_celedon.material, 'gold')

        thermos = Weapon.objects.get(slug='thermos-of-winds')
        self.assertEqual(thermos.owner_primary_character.slug, 'percy-jackson')
        war_chariot = Weapon.objects.get(slug='war-chariot')
        self.assertEqual(war_chariot.owner_primary_god.slug, 'ares')
        self.assertIsNone(war_chariot.owner_primary_character)
        cap = Weapon.objects.get(slug='cap-of-invisibility')
        self.assertEqual(cap.owner_primary_god.slug, 'hades')
        shield = Weapon.objects.get(slug='bronze-shield')
        self.assertEqual(shield.owner_primary_character.slug, 'perseus')
        self.assertEqual(shield.forged_by.slug, 'athena')

        rerun = StringIO()
        call_command('seed_items', stdout=rerun)
        self.assertEqual(Weapon.objects.count(), 40)
        self.assertIn('40 updated', rerun.getvalue())
