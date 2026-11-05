from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from apps.images.models import Image


class ImageCollectionViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.wiki_image = Image.objects.create(
            url='https://static.example/percy.jpg',
            thumbnail_url='https://static.example/percy-thumb.jpg',
            alt_text='Percy Jackson',
            source_type='wiki',
            source_url='https://riordan.fandom.com/wiki/Percy_Jackson',
            wiki_url='https://riordan.fandom.com/wiki/File:Percy.jpg',
        )
        self.official_image = Image.objects.create(
            url='https://example.org/cover.jpg',
            alt_text='Book cover',
            source_type='official_book',
        )

    def test_global_image_collection_returns_paginated_image_urls(self):
        response = self.client.get(reverse('image-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 2)
        result = next(item for item in response.data['data'] if item['id'] == self.wiki_image.id)
        self.assertEqual(result['url'], self.wiki_image.url)
        self.assertIsNone(result['license'])
        self.assertIsNone(result['license_url'])

    def test_global_collection_filters_wiki_images_by_source_and_file_page(self):
        response = self.client.get(
            reverse('image-list'),
            {
                'source_type': 'wiki',
                'source_url': 'https://riordan.fandom.com/wiki/Percy_Jackson',
                'wiki_url': 'https://riordan.fandom.com/wiki/File:Percy.jpg',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['id'], self.wiki_image.id)

    def test_global_collection_rejects_unknown_source_type(self):
        response = self.client.get(reverse('image-list'), {'source_type': 'unverified'})

        self.assertEqual(response.status_code, 400)
