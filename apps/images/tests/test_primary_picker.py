from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.characters.models import CharacterImage
from apps.images.models import Image
from apps.narrative.models import BookImage
from tests.makers import make_book, make_character


class PrimaryImagePickerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            username='picker-admin',
            email='picker-admin@example.com',
            password='test-password',
        )
        cls.picker_url = reverse('admin:images_image_primary_picker')

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.admin_user)

    @staticmethod
    def make_link(character, filename, *, is_primary=False):
        image = Image.objects.create(
            url=f'https://images.example.test/{filename}',
            thumbnail_url=f'https://images.example.test/thumbs/{filename}',
            alt_text=filename,
            source_type='wiki',
            category='other',
            source_url='https://riordan.fandom.com/wiki/Test',
        )
        return CharacterImage.objects.create(
            character=character,
            image=image,
            is_primary=is_primary,
            display_order=0,
        )

    def test_gallery_page_shows_thumbnails_and_primary_selection(self):
        character = make_character(name='Annabeth Chase')
        primary_link = self.make_link(character, 'Annabeth.jpg', is_primary=True)
        other_link = self.make_link(character, 'Annabeth_Concept.jpg')

        response = self.client.get(self.picker_url, {'entity': f'characters:{character.pk}'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Annabeth Chase')
        self.assertContains(response, 'https://images.example.test/thumbs/Annabeth.jpg')
        self.assertContains(response, 'https://images.example.test/thumbs/Annabeth_Concept.jpg')
        self.assertRegex(response.content.decode(), rf'value="{primary_link.pk}"\s+checked')
        self.assertContains(response, f'value="{other_link.pk}"')
        self.assertContains(response, 'No primary image')

    def test_book_gallery_uses_title_and_changelist_links_to_picker(self):
        book = make_book(title='The Lightning Thief')
        image = Image.objects.create(
            url='https://images.example.test/lightning-thief-cover.jpg',
            alt_text='The Lightning Thief cover',
            source_type='wiki',
            category='book_cover',
            source_url='https://riordan.fandom.com/wiki/The_Lightning_Thief',
        )
        BookImage.objects.create(book=book, image=image, display_order=0)

        response = self.client.get(self.picker_url, {'entity': f'books:{book.pk}'})
        changelist = self.client.get(reverse('admin:images_image_changelist'))

        self.assertContains(response, 'Books: The Lightning Thief')
        self.assertContains(response, 'The Lightning Thief cover')
        self.assertContains(changelist, 'Choose primary images')

    def test_saving_new_primary_clears_previous_choice_atomically(self):
        character = make_character(name='Percy Jackson')
        old_primary = self.make_link(character, 'Percy_Old.jpg', is_primary=True)
        new_primary = self.make_link(character, 'Percy_New.jpg')

        response = self.client.post(
            self.picker_url,
            {
                'entity': f'characters:{character.pk}',
                'primary_link_id': str(new_primary.pk),
            },
        )

        self.assertEqual(response.status_code, 302)
        old_primary.refresh_from_db()
        new_primary.refresh_from_db()
        self.assertFalse(old_primary.is_primary)
        self.assertTrue(new_primary.is_primary)
        self.assertEqual(
            CharacterImage.objects.filter(character=character, is_primary=True).count(), 1
        )

    def test_empty_selection_clears_primary(self):
        character = make_character(name='Grover Underwood')
        primary_link = self.make_link(character, 'Grover.jpg', is_primary=True)

        response = self.client.post(
            self.picker_url,
            {'entity': f'characters:{character.pk}', 'primary_link_id': ''},
        )

        self.assertEqual(response.status_code, 302)
        primary_link.refresh_from_db()
        self.assertFalse(primary_link.is_primary)

    def test_cannot_choose_image_from_another_entity_gallery(self):
        character = make_character(name='Thalia Grace')
        other_character = make_character(name='Nico di Angelo')
        current_primary = self.make_link(character, 'Thalia.jpg', is_primary=True)
        foreign_link = self.make_link(other_character, 'Nico.jpg')

        response = self.client.post(
            self.picker_url,
            {
                'entity': f'characters:{character.pk}',
                'primary_link_id': str(foreign_link.pk),
            },
        )

        self.assertEqual(response.status_code, 302)
        current_primary.refresh_from_db()
        foreign_link.refresh_from_db()
        self.assertTrue(current_primary.is_primary)
        self.assertFalse(foreign_link.is_primary)

    def test_invalid_primary_image_id_does_not_clear_existing_choice(self):
        character = make_character(name='Rachel Elizabeth Dare')
        primary_link = self.make_link(character, 'Rachel.jpg', is_primary=True)

        response = self.client.post(
            self.picker_url,
            {
                'entity': f'characters:{character.pk}',
                'primary_link_id': 'not-an-integer',
            },
        )

        self.assertEqual(response.status_code, 302)
        primary_link.refresh_from_db()
        self.assertTrue(primary_link.is_primary)

    def test_staff_without_image_change_permission_cannot_use_picker(self):
        staff_user = get_user_model().objects.create_user(
            username='read-only-staff',
            email='read-only@example.com',
            password='test-password',
            is_staff=True,
        )
        self.client.force_login(staff_user)

        response = self.client.get(self.picker_url)

        self.assertEqual(response.status_code, 403)
