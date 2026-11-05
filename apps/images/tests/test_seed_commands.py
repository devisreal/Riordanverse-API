import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.characters.models import CharacterImage
from apps.images.models import Image
from tests.makers import make_character


class SeedImagesCommandTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.data_file = Path(self.temp_dir.name) / 'images.json'
        self.payload = {
            'entities': [
                {
                    'entity_type': 'characters',
                    'entity_slug': 'percy-jackson',
                    'entity_name': 'Percy Jackson',
                    'source_page_url': 'https://riordan.fandom.com/wiki/Percy_Jackson',
                    'images': [
                        {
                            'file_title': 'File:Percy.jpg',
                            'url': 'https://static.example/percy.jpg',
                            'thumbnail_url': 'https://static.example/percy-thumb.jpg',
                            'alt_text': 'Percy Jackson',
                            'source_url': 'https://riordan.fandom.com/wiki/Percy_Jackson',
                            'wiki_url': 'https://riordan.fandom.com/wiki/File:Percy.jpg',
                            'width': 640,
                            'height': 480,
                            'file_format': 'jpg',
                        }
                    ],
                },
                {
                    'entity_type': 'events',
                    'entity_slug': 'lightning-thief',
                    'entity_name': 'The Lightning Thief',
                    'source_page_url': 'https://riordan.fandom.com/wiki/The_Lightning_Thief',
                    'images': [
                        {
                            'file_title': 'File:Cover.png',
                            'url': 'https://static.example/cover.png',
                            'alt_text': 'Cover',
                            'source_url': 'https://riordan.fandom.com/wiki/The_Lightning_Thief',
                            'wiki_url': 'https://riordan.fandom.com/wiki/File:Cover.png',
                        }
                    ],
                },
            ]
        }
        self.data_file.write_text(json.dumps(self.payload), encoding='utf-8')
        self.character = make_character(name='Percy Jackson')

    def test_seeds_wiki_image_metadata_and_supported_links_idempotently(self):
        with patch('apps.images.management.commands.seed_images.DATA_FILE', self.data_file):
            call_command('seed_images')

        percy_image = Image.objects.get(
            url='https://static.example/percy.jpg',
            source_url='https://riordan.fandom.com/wiki/Percy_Jackson',
        )
        self.assertEqual(percy_image.source_type, 'wiki')
        self.assertEqual(percy_image.category, 'other')
        self.assertIsNone(percy_image.license)
        self.assertIsNone(percy_image.license_url)
        self.assertEqual(percy_image.thumbnail_url, 'https://static.example/percy-thumb.jpg')
        self.assertEqual(percy_image.file_format, 'jpg')
        self.assertTrue(
            CharacterImage.objects.filter(character=self.character, image=percy_image).exists()
        )

        event_image = Image.objects.get(url='https://static.example/cover.png')
        self.assertEqual(event_image.source_type, 'wiki')
        self.assertIsNone(event_image.license)
        self.assertFalse(CharacterImage.objects.filter(image=event_image).exists())
        self.assertEqual(Image.objects.count(), 2)

        with patch('apps.images.management.commands.seed_images.DATA_FILE', self.data_file):
            call_command('seed_images')

        self.assertEqual(Image.objects.count(), 2)
        self.assertEqual(CharacterImage.objects.filter(character=self.character).count(), 1)
