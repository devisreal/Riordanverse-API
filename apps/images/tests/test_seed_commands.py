import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.bestiary.models import MonsterImage
from apps.characters.models import CharacterImage
from apps.divinities.models import GodImage
from apps.images.models import Image
from apps.items.models import WeaponImage
from apps.locations.models import LocationImage
from apps.narrative.models import BookImage
from tests.makers import (
    make_book,
    make_character,
    make_god,
    make_location,
    make_monster,
    make_weapon,
)


class SeedImagesCommandTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.data_file = Path(self.temp_dir.name) / 'images.json'
        self.overrides_file = Path(self.temp_dir.name) / 'image_gallery_overrides.json'
        self.overrides_file.write_text('{}', encoding='utf-8')
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
        with (
            patch('apps.images.management.commands.seed_images.DATA_FILE', self.data_file),
            patch(
                'apps.images.management.commands.seed_images.GALLERY_OVERRIDES_FILE',
                self.overrides_file,
            ),
        ):
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

    def test_curated_file_title_overrides_link_confirmed_zoe_images(self):
        zoe = make_character(name='Zoë Nightshade')
        source_url = 'https://riordan.fandom.com/wiki/Zoe_Nightshade'
        entries = [
            {
                'file_title': 'File:Huntress_constellation_GN.png',
                'url': 'https://static.example/Huntress_constellation_GN.png',
                'source_url': source_url,
            },
            {
                'file_title': 'File:Zoe_GN.png',
                'url': 'https://static.example/Zoe_GN.png',
                'source_url': source_url,
            },
        ]
        self.payload['entities'].append(
            {
                'entity_type': 'characters',
                'entity_slug': zoe.slug,
                'entity_name': zoe.name,
                'source_page_url': source_url,
                'images': entries,
            }
        )
        self.data_file.write_text(json.dumps(self.payload), encoding='utf-8')
        self.overrides_file.write_text(
            json.dumps(
                {
                    'characters': {
                        zoe.slug: {
                            'include_file_titles': [entry['file_title'] for entry in entries]
                        }
                    }
                }
            ),
            encoding='utf-8',
        )

        self._seed()

        for entry in entries:
            with self.subTest(file_title=entry['file_title']):
                image = Image.objects.get(url=entry['url'])
                self.assertTrue(CharacterImage.objects.filter(character=zoe, image=image).exists())
                self.assertFalse(
                    CharacterImage.objects.filter(character=self.character, image=image).exists()
                )

    def test_user_sourced_tyche_and_manticore_images_link_to_their_entities(self):
        tyche = make_god(name='Tyche')
        dr_thorn = make_monster(name='Dr. Thorn')
        tyche_source_url = 'https://riordan.fandom.com/wiki/Tyche%27s_Cabin'
        manticore_source_url = 'https://riordan.fandom.com/wiki/Manticore'
        tyche_image = {
            'file_title': 'File:Tyche.jpg',
            'url': 'https://static.wikia.nocookie.net/olympians/images/3/35/Tyche.jpg/revision/latest?cb=20140422034124',
            'source_url': tyche_source_url,
        }
        manticore_file_titles = [
            'File:Manticore-RR.jpg',
            'File:Manticore.jpg',
            'File:ManticoreSeaOfMonsters.jpg',
            'File:Manticore - GN (1).jpg',
            'File:Manticore - GN (2).jpg',
            'File:Manticore - GN (3).jpg',
            'File:Manticore - GN (4).jpg',
            'File:Manticore - GN (5).jpg',
            'File:Manticore GN.png',
        ]
        manticore_images = [
            {
                'file_title': file_title,
                'url': f'https://static.example/{file_title.removeprefix("File:")}',
                'source_url': manticore_source_url,
            }
            for file_title in manticore_file_titles
        ]
        self.payload['entities'].extend(
            [
                {
                    'entity_type': 'gods',
                    'entity_slug': tyche.slug,
                    'entity_name': tyche.name,
                    'source_page_url': 'https://riordan.fandom.com/wiki/Tyche',
                    'images': [tyche_image],
                },
                {
                    'entity_type': 'monsters',
                    'entity_slug': dr_thorn.slug,
                    'entity_name': dr_thorn.name,
                    'source_page_url': 'https://riordan.fandom.com/wiki/Dr._Thorn',
                    'images': manticore_images,
                },
            ]
        )
        self.data_file.write_text(json.dumps(self.payload), encoding='utf-8')
        self.overrides_file.write_text(
            json.dumps(
                {'monsters': {dr_thorn.slug: {'include_file_titles': manticore_file_titles}}}
            ),
            encoding='utf-8',
        )

        self._seed()

        tyche_image_row = Image.objects.get(url=tyche_image['url'])
        self.assertTrue(GodImage.objects.filter(god=tyche, image=tyche_image_row).exists())
        self.assertEqual(MonsterImage.objects.filter(monster=dr_thorn).count(), 9)

    def test_curated_book_image_is_linked_and_becomes_the_only_primary(self):
        book = make_book(title="Percy Jackson's Greek Heroes", book_number=99)
        source_url = "https://riordan.fandom.com/wiki/Percy_Jackson's_Greek_Heroes"
        old_cover = Image.objects.create(
            url='https://static.example/OldCover.jpg',
            source_url=source_url,
            source_type='wiki',
        )
        old_link = BookImage.objects.create(book=book, image=old_cover, is_primary=True)
        english_cover = {
            'file_title': 'File:Greekheroes.jpg',
            'url': 'https://static.example/Greekheroes.jpg',
            'thumbnail_url': 'https://static.example/Greekheroes-thumb.jpg',
            'alt_text': "English-language cover of Percy Jackson's Greek Heroes",
            'source_url': source_url,
            'width': 1195,
            'height': 1600,
            'file_format': 'jpg',
        }
        self.payload['entities'].append(
            {
                'entity_type': 'books',
                'entity_slug': book.slug,
                'entity_name': book.title,
                'source_page_url': source_url,
                'images': [
                    {
                        'file_title': 'File:OldCover.jpg',
                        'url': old_cover.url,
                        'source_url': source_url,
                        'width': 600,
                        'height': 900,
                    },
                    english_cover,
                ],
            }
        )
        self.data_file.write_text(json.dumps(self.payload), encoding='utf-8')
        self.overrides_file.write_text(
            json.dumps(
                {
                    'books': {
                        book.slug: {
                            'include_file_titles': ['File:Greekheroes.jpg'],
                            'primary_file_title': 'File:Greekheroes.jpg',
                        }
                    }
                }
            ),
            encoding='utf-8',
        )

        self._seed()

        english_image = Image.objects.get(url=english_cover['url'])
        english_link = BookImage.objects.get(book=book, image=english_image)
        old_link.refresh_from_db()
        self.assertTrue(english_link.is_primary)
        self.assertFalse(old_link.is_primary)
        self.assertEqual(BookImage.objects.filter(book=book, is_primary=True).count(), 1)
        self.assertEqual(english_image.thumbnail_url, english_cover['thumbnail_url'])
        self.assertEqual(english_image.category, 'book_cover')

    def test_excluded_ogygia_images_remain_global_but_are_not_gallery_links(self):
        location = make_location(name='Ogygia')
        source_url = 'https://riordan.fandom.com/wiki/Ogygia'
        entries = [
            {
                'file_title': 'File:Calypso-Viria.jpg',
                'url': 'https://static.example/Calypso-Viria.jpg',
                'source_url': source_url,
            },
            {
                'file_title': 'File:Moonlace.png',
                'url': 'https://static.example/Moonlace.png',
                'source_url': source_url,
            },
        ]
        for entry in entries:
            image = Image.objects.create(
                url=entry['url'],
                source_url=source_url,
                source_type='wiki',
            )
            LocationImage.objects.create(location=location, image=image)
        self.payload['entities'].append(
            {
                'entity_type': 'locations',
                'entity_slug': location.slug,
                'entity_name': location.name,
                'source_page_url': source_url,
                'images': entries,
            }
        )
        self.data_file.write_text(json.dumps(self.payload), encoding='utf-8')
        self.overrides_file.write_text(
            json.dumps(
                {
                    'locations': {
                        location.slug: {
                            'exclude_file_titles': [entry['file_title'] for entry in entries]
                        }
                    }
                }
            ),
            encoding='utf-8',
        )

        self._seed()

        self.assertEqual(
            Image.objects.filter(url__in=[entry['url'] for entry in entries]).count(), 2
        )
        self.assertFalse(LocationImage.objects.filter(location=location).exists())

    def test_failed_entity_import_preserves_existing_gallery_links(self):
        self.payload['entities'][0]['images'].append({'file_title': 'File:Missing.jpg'})
        self.data_file.write_text(json.dumps(self.payload), encoding='utf-8')

        self._seed()

        apollo_image = Image.objects.get(url__contains='Apollo_Viria.jpg')
        self.assertTrue(
            CharacterImage.objects.filter(character=self.character, image=apollo_image).exists()
        )
