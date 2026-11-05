# ty: ignore[unresolved-attribute]
from django.db import models

from apps.core.choices import IMAGE_CATEGORY_CHOICES, IMAGE_SOURCE_TYPE_CHOICES


class Image(models.Model):
    """URL-referenced image metadata; image files are not self-hosted."""

    url = models.URLField(
        max_length=2048,
        help_text='Direct URL to the image at its original source.',
    )
    thumbnail_url = models.URLField(
        max_length=2048,
        blank=True,
        null=True,
        help_text='Lower-resolution version for list views.',
    )
    alt_text = models.CharField(max_length=255, help_text='Accessible image description.')
    source_type = models.CharField(
        max_length=50,
        choices=IMAGE_SOURCE_TYPE_CHOICES,
        default='unknown',
    )
    category = models.CharField(
        max_length=50,
        choices=IMAGE_CATEGORY_CHOICES,
        default='other',
    )
    artist_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text='Credit for fan art or illustrated works.',
    )
    artist_url = models.URLField(
        max_length=2048,
        blank=True,
        null=True,
        help_text="Link to the artist's profile or portfolio.",
    )
    source_url = models.URLField(
        max_length=2048,
        blank=True,
        null=True,
        help_text='Original page where this image was found.',
    )
    license = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='e.g. "All Rights Reserved", "CC BY-NC"',
    )
    license_url = models.URLField(
        max_length=2048,
        blank=True,
        null=True,
        help_text='Canonical URL describing the image license.',
    )
    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)
    file_format = models.CharField(max_length=10, blank=True, null=True)
    wiki_url = models.URLField(
        max_length=2048, blank=True, null=True, help_text='Riordan Wiki image page reference.'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']  # noqa: RUF012

    def __str__(self):
        return f'{self.get_source_type_display()} — {self.get_category_display()} ({self.pk})'


class BaseImageLink(models.Model):
    """Abstract join-table fields shared by lore entity image relations."""

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='+')
    is_primary = models.BooleanField(
        default=False,
        help_text='Whether this is the main image used in list views and cards.',
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text='Controls gallery sequence. Lower numbers appear first.',
    )

    class Meta:
        abstract = True
        ordering = ['display_order']  # noqa: RUF012
