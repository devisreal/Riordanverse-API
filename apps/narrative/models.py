from autoslug import AutoSlugField
from django.db import models

from apps.core.choices import BOOK_TYPE_CHOICES, SERIES_CHOICES
from apps.core.models import BaseModel
from apps.images.models import BaseImageLink


class Book(BaseModel):
    """A novel, companion work, or other book in the Riordanverse."""

    slug = AutoSlugField(populate_from='title', unique=True, editable=True)
    title = models.CharField(max_length=255)
    series = models.CharField(
        max_length=50,
        choices=SERIES_CHOICES,
        default='percy_jackson_and_the_olympians',
    )
    book_number = models.PositiveIntegerField(
        help_text='Position in the series (1–5 for PJO core books).',
    )
    published_date = models.DateField(blank=True, null=True)
    synopsis = models.TextField(blank=True, null=True, help_text='Full plot summary.')
    short_description = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text='One-line tagline.',
    )
    book_type = models.CharField(
        max_length=50,
        choices=BOOK_TYPE_CHOICES,
        default='novel',
    )
    camp_bead_description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Description of the end-of-summer camp bead for this year.',
    )

    narrator = models.ForeignKey(
        'characters.Character',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='narrated_books',
        help_text='Percy Jackson for all PJO books.',
    )
    main_characters = models.ManyToManyField(
        'characters.Character',
        blank=True,
        related_name='books_as_main_character',
        help_text='Primary POV and quest characters.',
    )
    antagonists = models.ManyToManyField(
        'characters.Character',
        blank=True,
        related_name='books_as_antagonist',
        help_text='Primary villains, including demigods and Titans acting as antagonists.',
    )

    class Meta:
        ordering = ['series', 'book_number']  # noqa: RUF012
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        constraints = (
            models.UniqueConstraint(
                fields=['series', 'book_number'],
                name='unique_book_number_per_series',
            ),
        )

    def __str__(self):
        return self.title


class BookImage(BaseImageLink):
    """Join table linking a book to an image."""

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='images')

    class Meta(BaseImageLink.Meta):
        constraints = (
            models.UniqueConstraint(
                fields=['book'],
                condition=models.Q(is_primary=True),
                name='unique_primary_book_image',
            ),
        )
        verbose_name = 'Book Image'
        verbose_name_plural = 'Book Images'
