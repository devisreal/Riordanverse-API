from django.test import TestCase

from apps.characters.models import Character
from apps.search.adapters import CharacterSearchAdapter
from tests.makers import make_character


class SoftDeletedSearchTests(TestCase):
    def test_lore_search_adapter_excludes_soft_deleted_entities(self):
        character = make_character(name='Nico di Angelo')
        character.soft_delete()

        live_queryset = CharacterSearchAdapter(Character).get_live_queryset()

        self.assertIsNotNone(live_queryset)
        self.assertFalse(live_queryset.filter(pk=character.pk).exists())
        self.assertEqual(live_queryset.model, Character)
