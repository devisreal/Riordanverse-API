import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.characters.models import CharacterImage
from apps.images.models import Image
from apps.items.models import WeaponImage
from apps.narrative.models import BookImage
from tests.makers import make_book, make_character, make_weapon


class SeedImagesCommandTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.data_file = Path(self.temp_dir.name) / 'images.json'
        calypso_source_url = 'https://riordan.fandom.com/wiki/Calypso'
        lightning_thief_source_url = 'https://riordan.fandom.com/wiki/The_Lightning_Thief'
        self.payload = {
            'entities': [
                {
                    'entity_type': 'characters',
                    'entity_slug': 'calypso',
                    'entity_name': 'Calypso',
                    'source_page_url': calypso_source_url,
                    'images': [
                        {
                            'file_title': 'File:Apollo_Viria.jpg',
                            'url': 'https://static.example/Apollo_Viria.jpg/revision/latest?cb=1',
                            'thumbnail_url': 'https://static.example/Apollo_Viria-thumb.jpg',
                            'alt_text': 'Apollo Viria',
                            'source_url': calypso_source_url,
                            'wiki_url': 'https://riordan.fandom.com/wiki/File:Apollo_Viria.jpg',
                            'width': 640,
                            'height': 900,
                            'file_format': 'jpg',
                        },
                        {
                            'file_title': 'File:Calypso_RR.jpg',
                            'url': 'https://static.example/Calypso_RR.jpg/revision/latest?cb=2',
                            'thumbnail_url': 'https://static.example/Calypso_RR-thumb.jpg',
                            'alt_text': 'Calypso',
                            'source_url': calypso_source_url,
                            'wiki_url': 'https://riordan.fandom.com/wiki/File:Calypso_RR.jpg',
                            'width': 640,
                            'height': 900,
                            'file_format': 'jpg',
                        },
                    ],
                },
                {
                    'entity_type': 'books',
                    'entity_slug': 'the-lightning-thief',
                    'entity_name': 'The Lightning Thief',
                    'source_page_url': lightning_thief_source_url,
                    'images': [
                        {
                            'file_title': 'File:Coverart1.jpg',
                            'url': 'https://static.example/Coverart1.jpg/revision/latest?cb=3',
                            'alt_text': 'Cover art',
                            'source_url': lightning_thief_source_url,
                            'wiki_url': 'https://riordan.fandom.com/wiki/File:Coverart1.jpg',
                            'width': 600,
                            'height': 900,
                        },
                        {
                            'file_title': 'File:Ares.jpg',
                            'url': 'https://static.example/Ares.jpg/revision/latest?cb=4',
                            'alt_text': 'Ares',
                            'source_url': lightning_thief_source_url,
                            'wiki_url': 'https://riordan.fandom.com/wiki/File:Ares.jpg',
                            'width': 600,
                            'height': 900,
                        },
                    ],
                },
                {
                    'entity_type': 'weapons',
                    'entity_slug': 'riptide',
                    'entity_name': 'Riptide',
                    'source_page_url': 'https://riordan.fandom.com/wiki/Riptide',
                    'images': [
                        {
                            'file_title': 'File:Percy_Jackson.jpg',
                            'url': 'https://static.example/Percy_Jackson.jpg',
                            'source_url': 'https://riordan.fandom.com/wiki/Riptide',
                        },
                        {
                            'file_title': 'File:Riptide_Sword.jpg',
                            'url': 'https://static.example/Riptide_Sword.jpg',
                            'source_url': 'https://riordan.fandom.com/wiki/Riptide',
                        },
                    ],
                },
                {
                    'entity_type': 'events',
                    'entity_slug': 'lightning-thief',
                    'entity_name': 'The Lightning Thief event',
                    'source_page_url': lightning_thief_source_url,
                    'images': [
                        {
                            'file_title': 'File:Event.png',
                            'url': 'https://static.example/Event.png',
                            'alt_text': 'Event',
                            'source_url': lightning_thief_source_url,
                            'wiki_url': 'https://riordan.fandom.com/wiki/File:Event.png',
                        }
                    ],
                },
            ]
        }
        self.data_file.write_text(json.dumps(self.payload), encoding='utf-8')
        self.character = make_character(name='Calypso')
        self.book = make_book(title='The Lightning Thief')
        self.weapon = make_weapon(name='Riptide')

        wrong_image = Image.objects.create(
            url='https://static.example/Apollo_Viria.jpg/revision/latest?cb=1',
            source_url=calypso_source_url,
            source_type='wiki',
        )
        CharacterImage.objects.create(character=self.character, image=wrong_image)

    def _seed(self):
        with patch('apps.images.management.commands.seed_images.DATA_FILE', self.data_file):
            call_command('seed_images')

    def test_only_matching_character_and_book_cover_images_are_linked(self):
        self._seed()

        apollo_image = Image.objects.get(url__contains='Apollo_Viria.jpg')
        calypso_image = Image.objects.get(url__contains='Calypso_RR.jpg')
        cover_image = Image.objects.get(url__contains='Coverart1.jpg')
        ares_image = Image.objects.get(url__contains='Ares.jpg')
        event_image = Image.objects.get(url='https://static.example/Event.png')
        percy_image = Image.objects.get(url='https://static.example/Percy_Jackson.jpg')
        riptide_image = Image.objects.get(url='https://static.example/Riptide_Sword.jpg')

        self.assertFalse(
            CharacterImage.objects.filter(character=self.character, image=apollo_image).exists()
        )
        self.assertTrue(
            CharacterImage.objects.filter(character=self.character, image=calypso_image).exists()
        )
        self.assertTrue(BookImage.objects.filter(book=self.book, image=cover_image).exists())
        self.assertEqual(cover_image.category, 'book_cover')
        self.assertFalse(BookImage.objects.filter(book=self.book, image=ares_image).exists())
        self.assertFalse(CharacterImage.objects.filter(image=event_image).exists())
        self.assertFalse(WeaponImage.objects.filter(weapon=self.weapon, image=percy_image).exists())
        self.assertTrue(
            WeaponImage.objects.filter(weapon=self.weapon, image=riptide_image).exists()
        )
        self.assertEqual(Image.objects.count(), 7)

    def test_seed_is_idempotent_and_reconciles_stale_wiki_gallery_links(self):
        self._seed()
        self._seed()

        self.assertEqual(Image.objects.count(), 7)
        self.assertEqual(CharacterImage.objects.filter(character=self.character).count(), 1)
        self.assertEqual(BookImage.objects.filter(book=self.book).count(), 1)
        self.assertEqual(WeaponImage.objects.filter(weapon=self.weapon).count(), 1)

    def test_failed_entity_import_preserves_existing_gallery_links(self):
        self.payload['entities'][0]['images'].append({'file_title': 'File:Missing.jpg'})
        self.data_file.write_text(json.dumps(self.payload), encoding='utf-8')

        self._seed()

        apollo_image = Image.objects.get(url__contains='Apollo_Viria.jpg')
        self.assertTrue(
            CharacterImage.objects.filter(character=self.character, image=apollo_image).exists()
        )
