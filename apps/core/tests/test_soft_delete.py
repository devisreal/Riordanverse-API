from unittest.mock import Mock

from django.contrib import admin
from django.test import RequestFactory, TestCase

from apps.characters.admin import CharacterAdmin
from apps.characters.models import Character
from apps.core.models import LoreSource, LoreSourceType
from apps.core.seed_utils import update_or_create_by_expected_slug
from tests.makers import make_character


class SoftDeleteModelTests(TestCase):
    def test_instance_delete_hides_record_and_restore_makes_it_active(self):
        character = make_character(name='Percy Jackson')
        original_id = character.pk

        self.assertEqual(character.delete(), (1, {'characters.Character': 1}))
        deleted = Character.all_objects.get(pk=original_id)
        self.assertTrue(deleted.is_deleted)
        self.assertIsNotNone(deleted.deleted_at)
        self.assertFalse(Character.objects.filter(pk=original_id).exists())
        self.assertEqual(deleted.delete(), (0, {}))

        self.assertEqual(deleted.restore(), 1)
        deleted.refresh_from_db()
        self.assertFalse(deleted.is_deleted)
        self.assertIsNone(deleted.deleted_at)
        self.assertTrue(Character.objects.filter(pk=original_id).exists())

    def test_queryset_delete_soft_deletes_and_hard_delete_is_explicit(self):
        character = make_character(name='Annabeth Chase')
        character_id = character.pk

        deleted_count, details = Character.objects.filter(pk=character_id).delete()

        self.assertEqual(deleted_count, 1)
        self.assertEqual(details, {'characters.Character': 1})
        self.assertTrue(Character.all_objects.get(pk=character_id).is_deleted)
        self.assertEqual(Character.all_objects.filter(pk=character_id).hard_delete()[0], 1)
        self.assertFalse(Character.all_objects.filter(pk=character_id).exists())

    def test_restore_queryset_restores_deleted_rows(self):
        character = make_character(name='Grover Underwood')
        character.soft_delete()

        restored_count, details = Character.all_objects.filter(pk=character.pk).restore()

        self.assertEqual(restored_count, 1)
        self.assertEqual(details, {'characters.Character': 1})
        self.assertTrue(Character.objects.filter(pk=character.pk).exists())

    def test_seed_upsert_updates_deleted_canonical_row_without_restoring_it(self):
        character = make_character(name='Seeded Character')
        character.soft_delete()

        updated, created = update_or_create_by_expected_slug(
            Character,
            character.slug,
            {'name': 'Seeded Character'},
        )

        self.assertFalse(created)
        self.assertEqual(updated.pk, character.pk)
        self.assertTrue(updated.is_deleted)
        self.assertIsNotNone(updated.deleted_at)

    def test_lore_source_defaults_and_entity_relation(self):
        character = make_character(name='Thalia Grace')
        source = LoreSource.objects.create(
            title='The Titan’s Curse',
            source_type=LoreSourceType.PRIMARY_TEXT,
            citation='Chapter 13',
        )
        character.lore_sources.add(source)

        self.assertEqual(character.lore_accuracy, 'unreviewed')
        self.assertEqual(list(character.lore_sources.all()), [source])

    def test_admin_delete_hooks_soft_delete_and_admin_can_restore(self):
        character = make_character(name='Nico di Angelo')
        request = RequestFactory().post('/admin/characters/character/')
        model_admin = CharacterAdmin(Character, admin.site)

        model_admin.delete_model(request, character)

        self.assertFalse(Character.objects.filter(pk=character.pk).exists())
        self.assertTrue(model_admin.get_queryset(request).filter(pk=character.pk).exists())
        self.assertFalse(model_admin.has_delete_permission(request))

        model_admin.message_user = Mock()
        model_admin.restore_selected(
            request,
            Character.all_objects.filter(pk=character.pk),
        )
        self.assertTrue(Character.objects.filter(pk=character.pk).exists())
