# ruff: noqa: RUF012

from autoslug import AutoSlugField
from django.db import models

from apps.core.choices import (
    CHARACTER_TYPE_CHOICES,
    GENDER_CHOICES,
    GREEK_OR_ROMAN_CHOICES,
    SPECIES_CHOICES,
    STATUS_CHOICES,
)
from apps.core.models import BaseModel
from apps.images.models import BaseImageLink


class Character(BaseModel):
    """
    The central lore model. Covers demigods, mortals, satyrs, nymphs,
    hunters, oracles, centaurs, cyclopes, and non-god immortals.

    Edge cases handled:
    - Tyson: type=cyclops, is_demigod=False, divine_parent=Poseidon
    - Luke Castellan: affiliation is a JSONField list (multi-value),
      is_possessed=True in Books 4-5
    - Thalia Grace: special_states tracks tree transformation
    - Bianca/Nico: lore_notes covers Lotus Hotel time displacement
    - Rachel Dare: is_oracle=True after Book 5
    - Chiron: aliases=["Mr. Brunner", "Ronnie"]
    """

    slug = AutoSlugField(populate_from='name', unique=True, editable=False)
    name = models.CharField(max_length=255)

    # JSONField per important-notes.md note 1
    aliases = models.JSONField(
        default=list,
        help_text='["Wise Girl", "Seaweed Brain"]',
    )

    character_type = models.CharField(
        max_length=20,
        choices=CHARACTER_TYPE_CHOICES,
        default='demigod',
        db_column='type',
    )
    species = models.CharField(
        max_length=20,
        choices=SPECIES_CHOICES,
        default='demigod',
    )
    gender = models.CharField(
        max_length=15,
        choices=GENDER_CHOICES,
        default='unknown',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='alive',
    )
    greek_or_roman = models.CharField(
        max_length=10,
        choices=GREEK_OR_ROMAN_CHOICES,
        default='greek',
    )

    age_first_appearance = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text='Age at first book appearance.',
    )

    # Divine lineage
    divine_parent = models.ForeignKey(
        'divinities.God',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demigod_children',
        help_text='Olympian or minor god parent. Null for mortals and satyrs.',
    )
    divine_parent_titan = models.ForeignKey(
        'divinities.Titan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='character_children',
        help_text='Titan parent when the divine parent is not a God record.',
    )
    mortal_parent_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Name(s) of mortal parent(s) as plain text.',
    )
    mortal_parent_ref = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children_as_mortal_parent',
        help_text='FK to a named Character who is a mortal parent (e.g. Sally Jackson).',
    )

    # Self-referential relationships
    siblings = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True,
        help_text='Named siblings (divine and mortal).',
    )
    empathy_link = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empathy_link_partner',
        help_text='Character sharing an Empathy Link. Only Grover ↔ Percy in V1.',
    )

    # Camp Half-Blood
    cabin_number = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text='CHB cabin number. Null if not a camper.',
    )

    # Affiliation — JSONField list, multi-value per important-notes.md note 1
    # e.g. ["camp_half_blood", "kronos_army"] for Luke Castellan
    affiliation = models.JSONField(
        default=list,
        help_text='["camp_half_blood", "hunters_of_artemis"]',
    )

    fatal_flaw = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    # Weapons — string ref, unresolved until feature/items-app
    weapons = models.ManyToManyField(
        'items.Weapon',
        blank=True,
        related_name='wielded_by',
    )

    # Demigod traits
    can_see_through_mist = models.BooleanField(default=False)
    has_adhd = models.BooleanField(default=False)
    has_dyslexia = models.BooleanField(default=False)

    # Flags
    is_demigod = models.BooleanField(
        default=True,
        help_text='False for Tyson (Cyclops) and other non-demigod divine children.',
    )
    is_big_three_child = models.BooleanField(
        default=False,
        help_text='True for children of Zeus, Poseidon, or Hades.',
    )
    is_hunter_of_artemis = models.BooleanField(default=False)
    is_oracle = models.BooleanField(
        default=False,
        help_text='True for Rachel Dare after Book 5.',
    )
    is_possessed = models.BooleanField(
        default=False,
        help_text='True for Luke Castellan in Books 4–5 (possessed by Kronos).',
    )

    # Appearance — confirmed JSONField
    appearance = models.JSONField(
        default=dict,
        help_text=(
            '{"hair_color": "black", "hair_description": "jet-black, messy", '
            '"eye_color": "sea-green", "build": "lean", "height": "average for age", '
            '"notable_features": ["tan skin"]}'
        ),
    )

    # Personality — JSONField per important-notes.md note 1
    personality_traits = models.JSONField(
        default=list,
        help_text='["brave", "loyal", "sarcastic"]',
    )

    # Special states — confirmed structured JSONField
    special_states = models.JSONField(
        default=list,
        help_text=(
            '[{"state": "achilles_blessing", "description": "...", '
            '"active_from_book": 5, "active_to_book": 5}]'
        ),
    )

    quote = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text='Iconic quote from the character.',
    )
    description = models.TextField(blank=True, null=True)
    lore_notes = models.TextField(
        blank=True,
        null=True,
        help_text=(
            "Free-text field for nuances that don't fit structured fields. "
            'e.g. Bianca/Nico Lotus Hotel time displacement, Iapetus memory loss.'
        ),
    )

    # Books
    first_appearance_book = models.ForeignKey(
        'narrative.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='characters_first_appearing',
    )
    books_appeared_in = models.ManyToManyField(
        'narrative.Book',
        blank=True,
        related_name='characters',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Character'
        verbose_name_plural = 'Characters'
        constraints = [
            models.CheckConstraint(
                condition=~(
                    models.Q(divine_parent__isnull=False)
                    & models.Q(divine_parent_titan__isnull=False)
                ),
                name='character_single_divine_parent',
            )
        ]

    def __str__(self):
        return self.name


POWER_SOURCE_CHOICES = (
    ('divine_parent', 'Divine Parent'),
    ('blessing', 'Blessing'),
    ('curse', 'Curse'),
    ('training', 'Training'),
    ('item_granted', 'Item Granted'),
    ('creation', 'Creation'),
)

POWER_TYPE_CHOICES = (
    ('offensive', 'Offensive'),
    ('defensive', 'Defensive'),
    ('utility', 'Utility'),
    ('perception', 'Perception / Senses'),
    ('communication', 'Communication'),
    ('healing', 'Healing'),
    ('summoning', 'Summoning'),
    ('transformation', 'Transformation'),
    ('passive', 'Passive / Always Active'),
)


class Power(models.Model):
    """
    A named ability belonging to a Character.

    Does not inherit BaseModel — powers are not standalone lore entities.
    They are always accessed through their character.

    Example:
        {
            "name": "Hydrokinesis",
            "description": "Control over water",
            "source": "divine_parent",
            "scope": ["water", "sea", "ocean"],
            "limitations": "Weakened when far from water"
        }
    """

    character = models.ForeignKey(
        Character,
        on_delete=models.CASCADE,
        related_name='powers',
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(
        max_length=20,
        choices=POWER_SOURCE_CHOICES,
        blank=True,
        null=True,
    )
    type = models.CharField(
        max_length=20,
        choices=POWER_TYPE_CHOICES,
        default='utility',
    )
    # scope and limitations stored as JSONField per important-notes.md note 1
    scope = models.JSONField(
        default=list,
        help_text='["water", "sea", "ocean"]',
    )
    limitations = models.CharField(max_length=255, blank=True, null=True)
    is_passive = models.BooleanField(default=False)
    is_book_specific = models.BooleanField(default=False)
    first_demonstrated_book = models.ForeignKey(
        'narrative.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='powers_first_demonstrated',
    )
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Power'
        verbose_name_plural = 'Powers'

    def __str__(self):
        return f'{self.character.name} — {self.name}'


class CharacterImage(BaseImageLink):
    """Join table linking Character to Image."""

    character = models.ForeignKey(
        Character,
        on_delete=models.CASCADE,
        related_name='images',
    )

    class Meta(BaseImageLink.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['character'],
                condition=models.Q(is_primary=True),
                name='unique_primary_character_image',
            )
        ]
        verbose_name = 'Character Image'
        verbose_name_plural = 'Character Images'
