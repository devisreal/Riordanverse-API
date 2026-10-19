from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from tests.makers import make_book, make_character, make_location, make_monster


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
