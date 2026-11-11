from django.urls import reverse

from apps.core.models import LoreSource, LoreSourceType
from apps.core.tests.base import BaseAPITestCase
from apps.narrative.models import BookMainCharacter, BookNarrator
from apps.organizations.models import FactionMember
from tests.makers import (
    make_book,
    make_character,
    make_divine_relationship,
    make_faction,
    make_god,
    make_location,
)


class LoreMetadataAPITests(BaseAPITestCase):
    def test_list_filter_and_detail_expose_lore_provenance(self):
        source = LoreSource.objects.create(
            title='The Lightning Thief',
            source_type=LoreSourceType.PRIMARY_TEXT,
            citation='Chapter 3',
        )
        character = make_character(
            name='Percy Jackson',
            lore_accuracy='disputed',
            lore_notes='This seeded detail has conflicting interpretations.',
        )
        character.lore_sources.add(source)
        make_character(name='Annabeth Chase', lore_accuracy='confirmed')

        response = self.client.get(reverse('character-list'), {'lore_accuracy': 'disputed'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        list_item = response.data['data'][0]
        self.assertEqual(list_item['slug'], character.slug)
        self.assertEqual(list_item['lore_accuracy'], 'disputed')
        self.assertEqual(list_item['lore_notes'], character.lore_notes)
        self.assertEqual(list_item['lore_sources'][0]['title'], source.title)
        self.assertEqual(list_item['lore_sources'][0]['citation'], 'Chapter 3')

        detail = self.client.get(
            reverse('character-detail', kwargs={'slug': character.slug}),
        )
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['lore_accuracy'], 'disputed')
        self.assertEqual(detail.data['lore_sources'][0]['source_type'], 'primary_text')

    def test_invalid_lore_accuracy_filter_is_rejected(self):
        response = self.client.get(reverse('character-list'), {'lore_accuracy': 'headcanon'})

        self.assertEqual(response.status_code, 400)
        self.assertIn('valid_values', response.data['error'])

    def test_deleted_character_is_absent_from_list_and_detail(self):
        active = make_character(name='Percy Jackson')
        deleted = make_character(name='Annabeth Chase')
        deleted.soft_delete()

        response = self.client.get(reverse('character-list'))
        self.assertEqual(response.status_code, 200)
        slugs = {item['slug'] for item in response.data['data']}
        self.assertIn(active.slug, slugs)
        self.assertNotIn(deleted.slug, slugs)

        detail = self.client.get(
            reverse('character-detail', kwargs={'slug': deleted.slug}),
        )
        self.assertEqual(detail.status_code, 404)

    def test_deleted_typed_faction_member_is_not_exposed(self):
        faction = make_faction(name='Camp Half-Blood')
        member = make_character(name='Nico di Angelo')
        FactionMember.objects.create(faction=faction, member_character=member)
        member.soft_delete()

        response = self.client.get(
            reverse('faction-detail', kwargs={'slug': faction.slug}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['members'], [])
        self.assertEqual(response.data['member_slugs'], [])

    def test_deleted_book_cast_entities_are_not_exposed(self):
        book = make_book(title='The Lightning Thief')
        narrator = make_character(name='Percy Jackson')
        main_character = make_character(name='Annabeth Chase')
        BookNarrator.objects.create(book=book, character=narrator)
        BookMainCharacter.objects.create(book=book, character=main_character)
        narrator.soft_delete()
        main_character.soft_delete()

        response = self.client.get(reverse('book-detail', kwargs={'slug': book.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['narrators'], [])
        self.assertIsNone(response.data['narrator_slug'])
        self.assertEqual(response.data['narrator_slugs'], [])
        self.assertEqual(response.data['main_characters'], [])
        self.assertEqual(response.data['main_character_slugs'], [])

    def test_deleted_typed_controller_is_not_exposed(self):
        controller = make_god(name='Poseidon')
        location = make_location(name='Camp Half-Blood', controlled_by_god=controller)
        controller.soft_delete()

        response = self.client.get(
            reverse('location-detail', kwargs={'slug': location.slug}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['controlled_by'])

    def test_deleted_family_fk_is_not_exposed_in_character_payload(self):
        parent = make_god(name='Poseidon')
        child = make_character(name='Percy Jackson', divine_parent=parent)
        make_divine_relationship(parent, child)
        parent.soft_delete()

        response = self.client.get(
            reverse('character-detail', kwargs={'slug': child.slug}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['family']['parents'], [])

        list_response = self.client.get(reverse('character-list'))
        item = next(item for item in list_response.data['data'] if item['slug'] == child.slug)
        self.assertIsNone(item['divine_parent_slug'])
