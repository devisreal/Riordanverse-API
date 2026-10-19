from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from tests.makers import make_book, make_character


class EnvelopePaginationTests(BaseAPITestCase):
    """Exercise the shared pagination envelope through real API endpoints."""

    def setUp(self):
        super().setUp()
        for index in range(5):
            make_character(name=f'Character {index}')

    def test_list_response_has_data_key(self):
        response = self.client.get(reverse('character-list'))
        self.assertIn('data', response.data)

    def test_list_response_has_meta_key(self):
        response = self.client.get(reverse('character-list'))
        self.assertIn('meta', response.data)

    def test_meta_has_required_fields(self):
        response = self.client.get(reverse('character-list'))
        meta = response.data['meta']
        self.assertIn('total', meta)
        self.assertIn('page', meta)
        self.assertIn('limit', meta)
        self.assertIn('total_pages', meta)

    def test_meta_total_is_correct(self):
        response = self.client.get(reverse('character-list'))
        self.assertEqual(response.data['meta']['total'], 5)

    def test_meta_page_defaults_to_one(self):
        response = self.client.get(reverse('character-list'))
        self.assertEqual(response.data['meta']['page'], 1)

    def test_limit_parameter_is_respected(self):
        response = self.client.get(reverse('character-list'), {'limit': 2})
        self.assertEqual(len(response.data['data']), 2)
        self.assertEqual(response.data['meta']['limit'], 2)

    def test_page_parameter_is_respected(self):
        response = self.client.get(reverse('character-list'), {'limit': 2, 'page': 2})
        self.assertEqual(response.data['meta']['page'], 2)


class CustomExceptionHandlerTests(BaseAPITestCase):
    """Check the documented error envelope through real API endpoints."""

    def test_404_returns_error_envelope(self):
        response = self.client.get(reverse('character-detail', kwargs={'slug': 'nobody-here'}))
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.data)
        self.assertIn('code', response.data['error'])
        self.assertIn('message', response.data['error'])

    def test_404_code_is_not_found(self):
        response = self.client.get(reverse('character-detail', kwargs={'slug': 'nobody-here'}))
        self.assertEqual(response.data['error']['code'], 'NOT_FOUND')

    def test_400_returns_error_envelope(self):
        response = self.client.get(reverse('character-list'), {'status': 'invalid-status'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)


class StrictChoiceFilterTests(BaseAPITestCase):
    """Confirm invalid enum query values fail and valid values pass."""

    def setUp(self):
        super().setUp()
        make_character(name='Test Character')
        make_book(title='Test Book', book_number=1)

    def test_invalid_character_status_returns_400(self):
        response = self.client.get(reverse('character-list'), {'status': 'definitely-not-a-status'})
        self.assertEqual(response.status_code, 400)

    def test_invalid_character_type_returns_400(self):
        response = self.client.get(reverse('character-list'), {'character_type': 'wizard'})
        self.assertEqual(response.status_code, 400)

    def test_invalid_book_series_returns_400(self):
        response = self.client.get(reverse('book-list'), {'series': 'harry-potter'})
        self.assertEqual(response.status_code, 400)

    def test_valid_enum_does_not_return_400(self):
        response = self.client.get(reverse('character-list'), {'status': 'alive'})
        self.assertNotEqual(response.status_code, 400)
