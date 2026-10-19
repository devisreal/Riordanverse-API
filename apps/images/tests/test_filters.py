from django.urls import reverse

from apps.characters.models import CharacterImage
from apps.core.tests.base import BaseAPITestCase
from apps.images.models import Image
from tests.makers import make_character


def make_image(**kwargs):
    defaults = {
        'url': 'https://example.com/image.jpg',
        'alt_text': 'Test image',
    }
    defaults.update(kwargs)
    return Image.objects.create(**defaults)


class ImageFilterTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.character = make_character(name='Percy Jackson')
        self.official_image = make_image(
            url='https://example.com/official.jpg',
            source_type='official_book',
            category='portrait',
        )
        self.fan_art_image = make_image(
            url='https://example.com/fanart.jpg',
            source_type='fan_art',
            category='full_body',
        )
        CharacterImage.objects.create(
            character=self.character,
            image=self.official_image,
            is_primary=True,
            display_order=0,
        )
        CharacterImage.objects.create(
            character=self.character,
            image=self.fan_art_image,
            is_primary=False,
            display_order=1,
        )

    def test_filter_by_source_type(self):
        response = self.client.get(
            reverse('character-image-list', kwargs={'slug': 'percy-jackson'}),
            {'source_type': 'official_book'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['source_type'], 'official_book')

    def test_filter_by_category(self):
        response = self.client.get(
            reverse('character-image-list', kwargs={'slug': 'percy-jackson'}),
            {'category': 'full_body'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_invalid_source_type_returns_400(self):
        response = self.client.get(
            reverse('character-image-list', kwargs={'slug': 'percy-jackson'}),
            {'source_type': 'instagram'},
        )
        self.assertEqual(response.status_code, 400)

    def test_combined_filters(self):
        response = self.client.get(
            reverse('character-image-list', kwargs={'slug': 'percy-jackson'}),
            {'source_type': 'official_book', 'category': 'portrait'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
