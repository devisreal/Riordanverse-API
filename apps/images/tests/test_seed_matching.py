from django.test import SimpleTestCase

from apps.images.seed_matching import (
    image_url_matches_entity,
    is_book_cover,
    should_link_image,
)


class ImageSeedMatchingTests(SimpleTestCase):
    def test_matches_filename_not_revision_path_or_source_page(self):
        self.assertTrue(
            image_url_matches_entity(
                'https://static.example/images/Calypso_RR.jpg/revision/latest?cb=1',
                entity_name='Calypso',
                entity_slug='calypso',
            )
        )
        self.assertTrue(
            image_url_matches_entity(
                'https://static.example/CalypsoPortrait.jpg',
                entity_name='Calypso',
                entity_slug='calypso',
            )
        )
        self.assertFalse(
            image_url_matches_entity(
                'https://static.example/images/Apollo_Viria.jpg/revision/latest?cb=1',
                entity_name='Calypso',
                entity_slug='calypso',
            )
        )

    def test_matches_multiword_name_and_rejects_partial_name_tokens(self):
        self.assertTrue(
            image_url_matches_entity(
                'https://static.example/Percy_Jackson.jpg',
                entity_name='Percy Jackson',
                entity_slug='percy-jackson',
            )
        )
        self.assertTrue(
            image_url_matches_entity(
                'https://static.example/PercyJackson.jpg',
                entity_name='Percy Jackson',
                entity_slug='percy-jackson',
            )
        )
        self.assertFalse(
            image_url_matches_entity(
                'https://static.example/Annabeth_Chase.jpg',
                entity_name='Ann',
                entity_slug='ann',
            )
        )

    def test_each_entity_gallery_type_requires_a_filename_match(self):
        cases = (
            ('characters', 'Calypso', 'calypso', 'Calypso_Viria.jpg'),
            ('gods', 'Apollo', 'apollo', 'Apollo_Viria.jpg'),
            ('titans', 'Atlas', 'atlas', 'Atlas_GN.jpg'),
            ('weapons', 'Riptide', 'riptide', 'Riptide_sword.jpg'),
            ('monsters', 'Minotaur', 'minotaur', 'Minotaur.jpg'),
        )
        for entity_type, name, slug, filename in cases:
            with self.subTest(entity_type=entity_type):
                self.assertTrue(
                    should_link_image(
                        entity_type,
                        name,
                        slug,
                        {'url': f'https://static.example/{filename}'},
                    )
                )
                self.assertFalse(
                    should_link_image(
                        entity_type,
                        name,
                        slug,
                        {'url': 'https://static.example/Percy_Jackson.jpg'},
                    )
                )

    def test_book_cover_markers_and_title_named_portraits_are_kept(self):
        self.assertTrue(
            is_book_cover(
                {'url': 'https://static.example/Coverart1.jpg', 'width': 400, 'height': 600},
                book_title='The Lightning Thief',
                book_slug='the-lightning-thief',
            )
        )
        self.assertTrue(
            is_book_cover(
                {
                    'url': 'https://static.example/Italian_Lightning_Thief.jpg',
                    'width': 400,
                    'height': 600,
                },
                book_title='The Lightning Thief',
                book_slug='the-lightning-thief',
            )
        )

    def test_non_book_page_portraits_and_movie_covers_are_rejected(self):
        self.assertFalse(
            is_book_cover(
                {'url': 'https://static.example/Ares.jpg', 'width': 400, 'height': 600},
                book_title='The Lightning Thief',
                book_slug='the-lightning-thief',
            )
        )
        self.assertFalse(
            is_book_cover(
                {'url': 'https://static.example/Movie-cover-LT.jpg', 'width': 400, 'height': 600},
                book_title='The Lightning Thief',
                book_slug='the-lightning-thief',
            )
        )
        self.assertFalse(
            is_book_cover(
                {
                    'url': 'https://static.example/Lightning_Thief_artwork.jpg',
                    'width': 800,
                    'height': 600,
                },
                book_title='The Lightning Thief',
                book_slug='the-lightning-thief',
            )
        )
        self.assertFalse(
            is_book_cover(
                {
                    'url': 'https://static.example/Lightning_Thief_cover_concept.jpg',
                    'width': 400,
                    'height': 600,
                },
                book_title='The Lightning Thief',
                book_slug='the-lightning-thief',
            )
        )
