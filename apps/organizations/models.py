# ruff: noqa: RUF012

from autoslug import AutoSlugField
from django.db import models

from apps.core.choices import FACTION_TYPE_CHOICES
from apps.core.models import BaseModel

CABIN_POSITION_CHOICES = (
    ('left', 'Left side of camp (odd-numbered)'),
    ('right', 'Right side of camp (even-numbered)'),
)

FACTION_ALIGNMENT_CHOICES = (
    ('olympian', 'Olympian'),
    ('titan', 'Titan'),
    ('neutral', 'Neutral'),
    ('independent', 'Independent'),
)


# ---------------------------------------------------------------------------
# Cabin slug helper
# ---------------------------------------------------------------------------


def _cabin_slug(instance):
    """
    Produces slugs like 'cabin-3-poseidon'.
    Falls back to 'cabin-{number}' for honorary cabins with no deity.
    deity must be set before the first save when present.
    """
    if instance.deity:
        return f'cabin-{instance.number}-{instance.deity.slug}'
    return f'cabin-{instance.number}'


# ---------------------------------------------------------------------------
# Cabin
# ---------------------------------------------------------------------------


class Cabin(BaseModel):
    """
    One of the 20 Camp Half-Blood cabins.

    Cabins 1–12 are the original twelve Olympian cabins.
    Cabins 13–20 were added after the events of The Last Olympian
    when the minor gods were granted their own cabins.

    slug is produced by _cabin_slug: 'cabin-3-poseidon'.
    For honorary cabins (Hera #2, Artemis #8) with no deity,
    the slug falls back to 'cabin-{number}'.
    """

    slug = AutoSlugField(
        populate_from=_cabin_slug,
        unique=True,
        editable=False,
    )
    number = models.PositiveIntegerField(
        unique=True,
        help_text='Cabin number 1–20.',
    )
    deity = models.OneToOneField(
        'divinities.God',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cabin',
        help_text='The god this cabin honours. Null for honorary cabins.',
    )
    is_honorary = models.BooleanField(
        default=False,
        help_text='True for Hera (#2) and Artemis (#8) — no demigod children.',
    )
    is_empty = models.BooleanField(
        default=False,
        help_text='Whether this cabin currently has any campers.',
    )
    architecture_description = models.TextField(
        blank=True,
        null=True,
        help_text="Lore-accurate description of the cabin's appearance.",
    )
    position = models.CharField(
        max_length=10,
        choices=CABIN_POSITION_CHOICES,
        blank=True,
        null=True,
        help_text='Left (odd-numbered) or right (even-numbered) side of camp.',
    )

    # Known campers and head counselor
    known_campers = models.ManyToManyField(
        'characters.Character',
        blank=True,
        related_name='cabin',
        help_text='Named characters who live in this cabin.',
    )
    head_counselor = models.ForeignKey(
        'characters.Character',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='counselor_of_cabin',
        help_text='Current head counselor of this cabin.',
    )

    # When this cabin was added
    added_in_book = models.ForeignKey(
        'narrative.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cabins_added',
        help_text='Book in which this cabin was established. Null for original 12 (pre-series).',
    )

    class Meta:
        ordering = ['number']
        verbose_name = 'Cabin'
        verbose_name_plural = 'Cabins'

    def __str__(self):
        deity_name = self.deity.name if self.deity else 'Honorary'
        return f'Cabin {self.number} — {deity_name}'


# ---------------------------------------------------------------------------
# Faction
# ---------------------------------------------------------------------------


class Faction(BaseModel):
    """
    Named groups within the lore — camps, armies, councils, orders.

    leader uses two separate nullable FKs (same pattern as Location.controlled_by):
    - leader_character → characters.Character
    - leader_god → divinities.God
    A CheckConstraint prevents both being set simultaneously.
    Both null is valid for collective or leaderless factions.

    members is M2M → Character only — god members are modelled through
    their affiliation field on the God model rather than here.
    """

    slug = AutoSlugField(populate_from='name', unique=True, editable=False)
    name = models.CharField(max_length=255)
    faction_type = models.CharField(
        max_length=20,
        choices=FACTION_TYPE_CHOICES,
        default='group',
        db_column='type',
    )
    alignment = models.CharField(
        max_length=20,
        choices=FACTION_ALIGNMENT_CHOICES,
        default='olympian',
    )

    # Leader — two nullable FKs, at most one set
    leader_character = models.ForeignKey(
        'characters.Character',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_factions',
        help_text='Character leader of this faction.',
    )
    leader_god = models.ForeignKey(
        'divinities.God',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_factions',
        help_text='God leader of this faction.',
    )

    # Members — Character only
    members = models.ManyToManyField(
        'characters.Character',
        blank=True,
        related_name='factions',
        help_text='Named character members of this faction.',
    )

    books_active_in = models.ManyToManyField(
        'narrative.Book',
        blank=True,
        related_name='factions',
    )

    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Faction'
        verbose_name_plural = 'Factions'
        constraints = [
            # At most one leader — both null is valid (collective/leaderless)
            models.CheckConstraint(
                condition=~models.Q(
                    leader_character__isnull=False,
                    leader_god__isnull=False,
                ),
                name='faction_leader_not_both_set',
            ),
        ]

    def __str__(self):
        return self.name
