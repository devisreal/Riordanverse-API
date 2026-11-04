# ruff: noqa: RUF012

from autoslug import AutoSlugField
from django.db import models

from apps.core.choices import LOCATION_TYPE_CHOICES
from apps.core.models import BaseModel
from apps.images.models import BaseImageLink


class Location(BaseModel):
    """
    Named locations visited or referenced in V1.

    controlled_by uses three separate nullable FKs (Option A):
    - controlled_by_god → divinities.God
    - controlled_by_titan → divinities.Titan
    - controlled_by_character → characters.Character
    - controlled_by_monster → bestiary.Monster
    A CheckConstraint prevents more than one being set simultaneously.
    All null is valid for unclaimed, natural, or contested locations.

    notable_events is a JSONField per important-notes.md note 1.
    coordinates_approx is a plain CharField — promoted to lat/lng in V2
    if a map feature is introduced.
    """

    slug = AutoSlugField(populate_from='name', unique=True, editable=False)
    name = models.CharField(max_length=255)
    location_type = models.CharField(
        max_length=30,
        choices=LOCATION_TYPE_CHOICES,
        default='mortal_city',
        db_column='type',
    )
    real_world_location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Mortal equivalent e.g. "Long Island, New York".',
    )
    mythological_significance = models.TextField(
        blank=True,
        null=True,
        help_text='Why this place matters in Greek myth.',
    )
    is_hidden_from_mortals = models.BooleanField(
        default=False,
        help_text='Whether the Mist conceals this location from mortals.',
    )
    coordinates_approx = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Approximate real-world coordinates e.g. "40.7128° N, 74.0060° W". '
        'Promoted to proper lat/lng fields if a map feature is added in V2.',
    )

    # notable_events — JSONField per important-notes.md note 1
    notable_events = models.JSONField(
        default=list,
        help_text='["Percy defeats the Minotaur here", "Thalia\'s Pine marks the border"]',
    )

    # ---------------------------------------------------------------------------
    # controlled_by — Option A: three separate nullable FKs
    # ---------------------------------------------------------------------------
    controlled_by_god = models.ForeignKey(
        'divinities.God',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='controlled_locations',
        help_text='God who rules or inhabits this location.',
    )
    controlled_by_titan = models.ForeignKey(
        'divinities.Titan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='controlled_locations',
        help_text='Titan who rules or inhabits this location.',
    )
    controlled_by_character = models.ForeignKey(
        'characters.Character',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='controlled_locations',
        help_text='Character who rules or inhabits this location.',
    )
    controlled_by_monster = models.ForeignKey(
        'bestiary.Monster',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='controlled_locations',
        help_text='Monster who rules or inhabits this location.',
    )

    # Books
    books_appeared_in = models.ManyToManyField(
        'narrative.Book',
        blank=True,
        related_name='locations',
    )
    first_appearance_book = models.ForeignKey(
        'narrative.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locations_first_appearing',
    )
    first_appearance_locator = models.CharField(max_length=255, blank=True, null=True)
    earlier_mention_book = models.ForeignKey(
        'narrative.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locations_earlier_mentioned',
    )
    location_order = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Curated order based on first physical on-page appearance.',
    )

    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = [models.F('location_order').asc(nulls_last=True), 'name']
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
        constraints = [
            # At most one controller — all null is valid (unclaimed/natural)
            # but more than one set simultaneously is not
            models.CheckConstraint(
                condition=~(
                    models.Q(controlled_by_god__isnull=False)
                    & models.Q(controlled_by_titan__isnull=False)
                )
                & ~(
                    models.Q(controlled_by_god__isnull=False)
                    & models.Q(controlled_by_character__isnull=False)
                )
                & ~(
                    models.Q(controlled_by_titan__isnull=False)
                    & models.Q(controlled_by_character__isnull=False)
                )
                & ~(
                    models.Q(controlled_by_god__isnull=False)
                    & models.Q(controlled_by_monster__isnull=False)
                )
                & ~(
                    models.Q(controlled_by_titan__isnull=False)
                    & models.Q(controlled_by_monster__isnull=False)
                )
                & ~(
                    models.Q(controlled_by_character__isnull=False)
                    & models.Q(controlled_by_monster__isnull=False)
                ),
                name='location_controlled_by_at_most_one',
            ),
        ]

    def __str__(self):
        return self.name


class LocationImage(BaseImageLink):
    """Join table linking Location to Image."""

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='images',
    )

    class Meta(BaseImageLink.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['location'],
                condition=models.Q(is_primary=True),
                name='unique_primary_location_image',
            )
        ]
        verbose_name = 'Location Image'
        verbose_name_plural = 'Location Images'
