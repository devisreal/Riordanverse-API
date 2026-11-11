from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from apps.narrative.models import BookAntagonist, BookMainCharacter, BookNarrator
from tests.makers import (
    make_book,
    make_character,
    make_creature,
    make_god,
    make_location,
    make_monster,
    make_titan,
)


class BookModelTests(TestCase):
    def setUp(self):
        self.book = make_book(
            title='The Lightning Thief',
            series='percy_jackson_and_the_olympians',
            book_number=1,
        )

    def test_string_representation(self):
        self.assertEqual(str(self.book), 'The Lightning Thief')

    def test_slug_generated_from_title(self):
        self.assertEqual(self.book.slug, 'the-lightning-thief')

    def test_book_number_is_unique_per_series(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_book(
                title='Duplicate Book',
                series='percy_jackson_and_the_olympians',
                book_number=1,
            )

    def test_main_characters_many_to_many(self):
        percy = make_character(name='Percy Jackson')
        self.book.main_characters.add(percy)
        self.assertIn(percy, self.book.main_characters.all())

    def test_parent_collection_relationship_has_reverse_included_stories(self):
        collection = make_book(
            title='The Demigod Files',
            series='companion',
            book_number=1,
            book_type='short_story_collection',
        )
        story = make_book(
            title='The Sword of Hades',
            series='companion',
            book_number=2,
            book_type='short_story',
            parent_collection=collection,
        )
        self.assertEqual(story.parent_collection, collection)
        self.assertIn(story, collection.included_stories.all())


class BookTypedCastModelTests(TestCase):
    def setUp(self):
        self.book = make_book(title='The Lightning Thief', book_number=1)

    def test_typed_main_characters_and_antagonists_support_all_entity_types(self):
        entities = (
            ('character', make_character(name='Percy Jackson')),
            ('god', make_god(name='Ares')),
            ('titan', make_titan(name='Atlas')),
            ('monster', make_monster(name='Medusa')),
            ('creature', make_creature(name='Myrmekes')),
        )
        for entity_type, entity in entities:
            BookMainCharacter.objects.create(book=self.book, **{entity_type: entity})
            BookAntagonist.objects.create(book=self.book, **{entity_type: entity})

        self.assertEqual(self.book.main_character_records.count(), 5)
        self.assertEqual(self.book.antagonist_records.count(), 5)
        self.assertEqual(
            list(self.book.main_characters.values_list('slug', flat=True)), ['percy-jackson']
        )
        self.assertEqual(
            list(self.book.antagonists.values_list('slug', flat=True)), ['percy-jackson']
        )

    def test_typed_links_require_exactly_one_entity(self):
        for link_model in (BookMainCharacter, BookAntagonist):
            with (
                self.subTest(link_model=link_model.__name__),
                self.assertRaises(IntegrityError),
                transaction.atomic(),
            ):
                link_model.objects.create(book=self.book)

    def test_typed_links_reject_multiple_entity_types(self):
        for link_model in (BookMainCharacter, BookAntagonist):
            with (
                self.subTest(link_model=link_model.__name__),
                self.assertRaises(IntegrityError),
                transaction.atomic(),
            ):
                link_model.objects.create(
                    book=self.book,
                    character=make_character(),
                    god=make_god(),
                )


class BookTypedNarratorModelTests(TestCase):
    def setUp(self):
        self.book = make_book(title='Narrator Model Book', book_number=1)

    def test_typed_narrators_support_all_entity_types_and_character_compatibility(self):
        entities = (
            ('character', make_character(name='Percy Jackson')),
            ('god', make_god(name='Apollo')),
            ('titan', make_titan(name='Atlas')),
            ('monster', make_monster(name='Medusa')),
            ('creature', make_creature(name='Myrmekes')),
        )
        for entity_type, entity in entities:
            BookNarrator.objects.create(book=self.book, **{entity_type: entity})

        self.assertEqual(self.book.narrator_records.count(), 5)
        self.assertEqual(
            list(self.book.narrators.values_list('slug', flat=True)), ['percy-jackson']
        )

    def test_typed_narrators_require_exactly_one_entity(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            BookNarrator.objects.create(book=self.book)

        with self.assertRaises(IntegrityError), transaction.atomic():
            BookNarrator.objects.create(
                book=self.book,
                character=make_character(),
                god=make_god(),
            )

    def test_typed_narrator_links_reject_duplicates(self):
        percy = make_character(name='Percy Jackson')
        BookNarrator.objects.create(book=self.book, character=percy)
        with self.assertRaises(IntegrityError), transaction.atomic():
            BookNarrator.objects.create(book=self.book, character=percy)


class BookHierarchyViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.collection = make_book(
            title='The Demigod Files',
            series='companion',
            book_number=1,
            book_type='short_story_collection',
        )
        self.story = make_book(
            title='The Sword of Hades',
            series='companion',
            book_number=2,
            book_type='short_story',
            parent_collection=self.collection,
        )

    def test_story_detail_includes_parent_collection_summary(self):
        response = self.client.get(reverse('book-detail', kwargs={'slug': self.story.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['parent_collection']['slug'], self.collection.slug)
        self.assertEqual(response.data['parent_collection']['title'], self.collection.title)
        self.assertEqual(response.data['parent_collection']['book_type'], 'short_story_collection')

    def test_collection_detail_includes_story_summaries(self):
        response = self.client.get(reverse('book-detail', kwargs={'slug': self.collection.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['included_stories']), 1)
        self.assertEqual(response.data['included_stories'][0]['slug'], self.story.slug)

    def test_filter_by_parent_collection_slug(self):
        response = self.client.get(
            reverse('book-list'), {'parent-collection': self.collection.slug}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([book['slug'] for book in response.data['data']], [self.story.slug])


class BookListViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.book = make_book(title='The Lightning Thief', book_number=1)

    def test_list_returns_200_and_data_envelope(self):
        response = self.client.get(reverse('book-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.data)
        self.assertIn('meta', response.data)

    def test_detail_returns_200(self):
        response = self.client.get(reverse('book-detail', kwargs={'slug': 'the-lightning-thief'}))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_404_for_unknown(self):
        response = self.client.get(reverse('book-detail', kwargs={'slug': 'no-such-book'}))
        self.assertEqual(response.status_code, 404)

    def test_detail_returns_typed_casts_and_character_only_slug_fields(self):
        entities = (
            ('character', make_character(name='Percy Jackson')),
            ('god', make_god(name='Ares')),
            ('titan', make_titan(name='Atlas')),
            ('monster', make_monster(name='Medusa')),
            ('creature', make_creature(name='Myrmekes')),
        )
        for entity_type, entity in entities:
            BookMainCharacter.objects.create(book=self.book, **{entity_type: entity})
            BookAntagonist.objects.create(book=self.book, **{entity_type: entity})
            BookNarrator.objects.create(book=self.book, **{entity_type: entity})
        self.book.narrator = entities[0][1]
        self.book.save(update_fields=['narrator'])

        response = self.client.get(reverse('book-detail', kwargs={'slug': self.book.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item['type'] for item in response.data['main_characters']], [e[0] for e in entities]
        )
        self.assertEqual(
            [item['type'] for item in response.data['antagonists']], [e[0] for e in entities]
        )
        self.assertEqual(response.data['main_character_slugs'], ['percy-jackson'])
        self.assertEqual(response.data['antagonist_slugs'], ['percy-jackson'])
        self.assertIsNone(response.data['narrator_slug'])
        self.assertEqual(response.data['narrator_slugs'], ['percy-jackson'])
        self.assertEqual(
            [item['type'] for item in response.data['narrators']], [e[0] for e in entities]
        )

    def test_filter_by_typed_main_character_and_antagonist(self):
        creature = make_creature(name='Myrmekes')
        god = make_god(name='Ares')
        BookMainCharacter.objects.create(book=self.book, creature=creature)
        BookAntagonist.objects.create(book=self.book, god=god)

        main_response = self.client.get(
            reverse('book-list'), {'main_character_creature': creature.slug}
        )
        antagonist_response = self.client.get(reverse('book-list'), {'antagonist_god': god.slug})

        self.assertEqual([item['slug'] for item in main_response.data['data']], [self.book.slug])
        self.assertEqual(
            [item['slug'] for item in antagonist_response.data['data']], [self.book.slug]
        )

    def test_detail_projects_legacy_narrator_into_typed_fields(self):
        percy = make_character(name='Percy Jackson')
        self.book.narrator = percy
        self.book.save(update_fields=['narrator'])

        response = self.client.get(reverse('book-detail', kwargs={'slug': self.book.slug}))

        self.assertEqual(response.data['narrator_slug'], 'percy-jackson')
        self.assertEqual(response.data['narrator_slugs'], ['percy-jackson'])
        self.assertEqual(
            response.data['narrators'],
            [{'type': 'character', 'slug': 'percy-jackson', 'name': 'Percy Jackson'}],
        )

    def test_filter_by_typed_narrator(self):
        entities = (
            ('narrator_character', make_character(name='Percy Jackson')),
            ('narrator_god', make_god(name='Apollo')),
            ('narrator_titan', make_titan(name='Atlas')),
            ('narrator_monster', make_monster(name='Medusa')),
            ('narrator_creature', make_creature(name='Myrmekes')),
        )
        for parameter, entity in entities:
            entity_type = parameter.removeprefix('narrator_')
            BookNarrator.objects.create(book=self.book, **{entity_type: entity})

        for parameter, entity in entities:
            with self.subTest(entity_type=parameter):
                response = self.client.get(reverse('book-list'), {parameter: entity.slug})
                self.assertEqual(response.status_code, 200)
                self.assertEqual([item['slug'] for item in response.data['data']], [self.book.slug])

        legacy_response = self.client.get(reverse('book-list'), {'narrator': entities[0][1].slug})
        self.assertEqual([item['slug'] for item in legacy_response.data['data']], [self.book.slug])

    def test_filter_by_series(self):
        response = self.client.get(
            reverse('book-list'), {'series': 'percy_jackson_and_the_olympians'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_invalid_series_returns_400(self):
        response = self.client.get(reverse('book-list'), {'series': 'lord-of-the-rings'})
        self.assertEqual(response.status_code, 400)

    def test_book_character_subresource(self):
        character = make_character(name='Percy Jackson')
        character.books_appeared_in.add(self.book)
        response = self.client.get(reverse('book-character-list', kwargs={'slug': self.book.slug}))
        self.assertEqual(response.status_code, 200)
        slugs = [character['slug'] for character in response.data['data']]
        self.assertIn('percy-jackson', slugs)

    def test_book_monster_subresource(self):
        monster = make_monster(name='Medusa')
        monster.books_appeared_in.add(self.book)
        response = self.client.get(reverse('book-monster-list', kwargs={'slug': self.book.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertIn(monster.slug, [item['slug'] for item in response.data['data']])

    def test_book_location_subresource(self):
        location = make_location(name='Camp Half-Blood')
        location.books_appeared_in.add(self.book)
        response = self.client.get(reverse('book-location-list', kwargs={'slug': self.book.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertIn(location.slug, [item['slug'] for item in response.data['data']])
