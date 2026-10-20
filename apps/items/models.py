# ruff: noqa: RUF012

from autoslug import AutoSlugField
from django.db import models

from apps.core.choices import MATERIAL_CHOICES, WEAPON_TYPE_CHOICES
from apps.core.models import BaseModel
from apps.images.models import BaseImageLink


class Weapon(BaseModel):
    """
    Covers divine weapons, demigod weapons, and magical artifacts.

    The distinction between a weapon and a magical item is handled by
    weapon_type — e.g. sword, dagger vs. magical_item, artifact.

    Owner polymorphism uses three separate nullable FKs:
    - owner_primary_character → characters.Character
    - owner_primary_god → divinities.God
    - owner_primary_titan → divinities.Titan
    A CheckConstraint prevents more than one from being set simultaneously.
    All null is valid for unclaimed artifacts.

    owner_history is a JSONField for narrative flavour — not queryable
    via filter but surfaced in the detail response.

    Forgers can be either a God or Character; forged_by_notes handles
    non-entity forgers such as Cyclopes under Hephaestus's direction.
    """

    slug = AutoSlugField(populate_from='name', unique=True, editable=False)
    name = models.CharField(max_length=255)
    true_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Ancient name e.g. "Anaklusmos" for Riptide.',
    )
    weapon_type = models.CharField(
        max_length=20,
        choices=WEAPON_TYPE_CHOICES,
        default='sword',
        db_column='type',
    )
    material = models.CharField(
        max_length=20,
        choices=MATERIAL_CHOICES,
        blank=True,
        null=True,
    )

    # JSONField per important-notes.md note 1
    form = models.JSONField(
        default=list,
        help_text='["ballpoint pen", "sword"]',
    )
    abilities = models.JSONField(
        default=list,
        help_text='["always returns to owner", "passes through mortals"]',
    )

    transforms = models.BooleanField(
        default=False,
        help_text='Whether this weapon/item can change form.',
    )
    transform_trigger = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='How transformation is activated e.g. "uncapping the pen".',
    )
    passes_through_mortals = models.BooleanField(
        default=False,
        help_text='True for Celestial Bronze weapons.',
    )

    # ---------------------------------------------------------------------------
    # Ownership — Option B: separate nullable FKs per entity type
    # ---------------------------------------------------------------------------
    owner_primary_character = models.ForeignKey(
        'characters.Character',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_weapons',
        help_text='Current primary owner if a Character.',
    )
    owner_primary_god = models.ForeignKey(
        'divinities.God',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_weapons',
        help_text='Current primary owner if a God.',
    )
    owner_primary_titan = models.ForeignKey(
        'divinities.Titan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_weapons',
        help_text='Current primary owner if a Titan.',
    )

    # Structured JSONField — narrative flavour, not filterable
    owner_history = models.JSONField(
        default=list,
        help_text=(
            '[{"type": "character", "slug": "luke-castellan", "notes": "Original wielder"},'
            ' {"type": "god", "slug": "hephaestus", "notes": "Forged and gifted"}]'
        ),
    )

    # ---------------------------------------------------------------------------
    # Provenance
    # ---------------------------------------------------------------------------
    forged_by = models.ForeignKey(
        'divinities.God',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='forged_weapons',
        help_text='God who forged or created this weapon.',
    )
    forged_by_character = models.ForeignKey(
        'characters.Character',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='forged_weapons',
        help_text='Character who forged or created this weapon.',
    )
    forged_by_notes = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='e.g. "Forged by the Cyclopes under Hephaestus\'s direction".',
    )
    origin_story = models.TextField(
        blank=True,
        null=True,
        help_text='How this weapon was made or obtained.',
    )

    # Books
    first_appearance_book = models.ForeignKey(
        'narrative.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='weapons_first_appearing',
    )
    books_appeared_in = models.ManyToManyField(
        'narrative.Book',
        blank=True,
        related_name='weapons',
    )

    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Weapon / Magical Item'
        verbose_name_plural = 'Weapons & Magical Items'
        constraints = [
            models.CheckConstraint(
                condition=(
                    ~models.Q(
                        owner_primary_character__isnull=False,
                        owner_primary_god__isnull=False,
                    )
                    & ~models.Q(
                        owner_primary_character__isnull=False,
                        owner_primary_titan__isnull=False,
                    )
                    & ~models.Q(
                        owner_primary_god__isnull=False,
                        owner_primary_titan__isnull=False,
                    )
                ),
                name='weapon_owner_primary_at_most_one_set',
            ),
            models.CheckConstraint(
                condition=~models.Q(
                    forged_by__isnull=False,
                    forged_by_character__isnull=False,
                ),
                name='weapon_forged_by_at_most_one_set',
            ),
        ]

    def __str__(self):
        return self.name


class WeaponImage(BaseImageLink):
    """Join table linking Weapon to Image."""

    weapon = models.ForeignKey(
        Weapon,
        on_delete=models.CASCADE,
        related_name='images',
    )

    class Meta(BaseImageLink.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['weapon'],
                condition=models.Q(is_primary=True),
                name='unique_primary_weapon_image',
            )
        ]
        verbose_name = 'Weapon Image'
        verbose_name_plural = 'Weapon Images'
