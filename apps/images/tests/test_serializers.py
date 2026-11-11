from django.test import TestCase

from apps.images.models import Image
from apps.images.serializers import ImageListSerializer, ImageSerializer


class ImageLicenseSerializerTests(TestCase):
    def setUp(self):
        self.image = Image.objects.create(
            url='https://images.example.org/hero.jpg',
            alt_text='Hero portrait',
            source_type='wiki',
            artist_name='Artist',
            artist_url='https://riordan.fandom.com/wiki/User:Artist',
            source_url='https://riordan.fandom.com/wiki/Percy_Jackson',
            license='CC BY 4.0',
            license_url='https://creativecommons.org/licenses/by/4.0/',
            wiki_url='https://riordan.fandom.com/wiki/File:Hero.jpg',
        )

    def test_detail_serializer_exposes_license_url_and_source_attribution(self):
        payload = ImageSerializer(self.image).data

        self.assertEqual(payload['license'], 'CC BY 4.0')
        self.assertEqual(payload['license_url'], 'https://creativecommons.org/licenses/by/4.0/')
        self.assertEqual(payload['source_url'], 'https://riordan.fandom.com/wiki/Percy_Jackson')
        self.assertEqual(payload['artist_url'], 'https://riordan.fandom.com/wiki/User:Artist')

    def test_embedded_image_serializer_exposes_license_and_attribution(self):
        payload = ImageListSerializer(self.image).data

        self.assertEqual(payload['license'], 'CC BY 4.0')
        self.assertEqual(payload['license_url'], 'https://creativecommons.org/licenses/by/4.0/')
        self.assertEqual(payload['source_url'], 'https://riordan.fandom.com/wiki/Percy_Jackson')
        self.assertEqual(payload['artist_url'], 'https://riordan.fandom.com/wiki/User:Artist')
