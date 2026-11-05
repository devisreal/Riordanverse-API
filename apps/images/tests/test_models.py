from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.images.models import Image
from tests.makers import make_character


def make_image(**kwargs):
    defaults = {
        'url': 'https://example.com/image.jpg',
        'alt_text': 'Test image',
    }
    defaults.update(kwargs)
    return Image.objects.create(**defaults)


class ImageModelTests(TestCase):
    def test_str_includes_choice_displays(self):
        image = make_image(source_type='official_book', category='portrait')
        self.assertIn('Official Book', str(image))
        self.assertIn('Portrait', str(image))

    def test_source_type_default(self):
        image = make_image()
        self.assertEqual(image.source_type, 'unknown')

    def test_category_default(self):
        image = make_image()
        self.assertEqual(image.category, 'other')

    def test_optional_fields_are_nullable(self):
        image = make_image()
        self.assertIsNone(image.thumbnail_url)
        self.assertIsNone(image.artist_name)
        self.assertIsNone(image.artist_url)
        self.assertIsNone(image.source_url)
        self.assertIsNone(image.license)
        self.assertIsNone(image.license_url)

    def test_character_image_join(self):
        from apps.characters.models import CharacterImage

        character = make_character(name='Percy Jackson')
        image = make_image()
        CharacterImage.objects.create(
            character=character,
            image=image,
            is_primary=True,
            display_order=0,
        )

        self.assertEqual(character.images.count(), 1)
        self.assertTrue(character.images.first().is_primary)

    def test_primary_character_image_unique_constraint(self):
        from apps.characters.models import CharacterImage

        character = make_character(name='Annabeth Chase')
        image_one = make_image(url='https://example.com/1.jpg')
        image_two = make_image(url='https://example.com/2.jpg')
        CharacterImage.objects.create(character=character, image=image_one, is_primary=True)

        with self.assertRaises(IntegrityError), transaction.atomic():
            CharacterImage.objects.create(character=character, image=image_two, is_primary=True)
