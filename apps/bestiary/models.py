# ruff: noqa: RUF012

from autoslug import AutoSlugField
from django.db import models

from apps.core.choices import (
    MONSTER_ALLEGIANCE_CHOICES,
    MONSTER_TYPE_CHOICES,
)
from apps.core.models import BaseModel
from apps.images.models import BaseImageLink

CREATURE_ALIGNMENT_CHOICES = (
    ('olympian', 'Olympian Aligned'),
    ('titan', 'Titan Aligned'),
    ('neutral', 'Neutral'),
    ('independent', 'Independent'),
    ('varies', 'Varies'),
)


# ---------------------------------------------------------------------------
# Monster
# ---------------------------------------------------------------------------


class Monster(BaseModel):
    """
    Named individual monsters encountered in V1.

    Covers everything from Medusa and the Minotaur to Typhon and Kampê.
    Distinct from Creature which models species/types rather than individuals.

    aliases and abilities use JSONField per important-notes.md note 1.
    Character defeat events are stored through MonsterDefeat; God links remain
    separate until God defeat events receive their own event model.
    """

    slug = AutoSlugField(populate_from='name', unique=True, editable=False)
    name = models.CharField(max_length=255)

    # JSONField per important-notes.md note 1
    aliases = models.JSONField(
        default=list,
        help_text='["Aunty Em"] for Medusa, ["Dr. Thorn"] for the Manticore',
    )

    monster_type = models.CharField(
        max_length=30,
        choices=MONSTER_TYPE_CHOICES,
        default='chimeric',
        db_column='type',
    )
    allegiance = models.CharField(
        max_length=20,
        choices=MONSTER_ALLEGIANCE_CHOICES,
        default='independent',
    )

    origin_myth = models.TextField(
        blank=True,
        null=True,
        help_text='The original Greek myth origin story.',
    )
    physical_description = models.TextField(
        blank=True,
        null=True,
        help_text='Physical appearance as described in the series.',
    )

    # JSONField per important-notes.md note 1
    abilities = models.JSONField(
        default=list,
        help_text='["petrifying gaze", "flight"]',
    )
    weaknesses = models.JSONField(
        default=list,
        help_text='["mirrors", "celestial bronze"]',
    )
    notable_victims = models.JSONField(
        default=list,
        help_text='["Bianca di Angelo", "Lee Fletcher"]',
    )

    # Reform mechanics
    can_reform = models.BooleanField(
        default=True,
        help_text='Whether this monster reforms after death.',
    )
    reform_time = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='e.g. "months", "days", "instantly"',
    )
    reform_location = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        default='Tartarus',
    )

    spoils_of_war = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Trophy left behind on death e.g. Nemean Lion pelt.',
    )
    parent_entity = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Mythological parentage e.g. "Phorcys and Ceto" for Medusa.',
    )
    disguise_form = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Human disguise used e.g. "Middle Eastern woman running garden centre".',
    )

    # Defeat events — M2M → Character through MonsterDefeat
    defeated_by = models.ManyToManyField(
        'characters.Character',
        through='MonsterDefeat',
        blank=True,
        related_name='+',
        help_text='Characters who defeat or decisively subdue this monster.',
    )
    defeated_by_gods = models.ManyToManyField(
        'divinities.God',
        blank=True,
        related_name='monsters_defeated',
        help_text='Gods who ultimately defeat this monster.',
    )

    # Books
    first_appearance_book = models.ForeignKey(
        'narrative.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='monsters_first_appearing',
    )
    books_appeared_in = models.ManyToManyField(
        'narrative.Book',
        blank=True,
        related_name='monsters',
    )

    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Monster'
        verbose_name_plural = 'Monsters'

    def __str__(self):
        return self.name


class MonsterDefeat(models.Model):
    """A distinct event in which a Character defeats or subdues a Monster."""

    monster = models.ForeignKey(
        Monster,
        on_delete=models.CASCADE,
        related_name='defeats',
    )
    defeated_by = models.ForeignKey(
        'characters.Character',
        on_delete=models.CASCADE,
        related_name='monsters_defeated',
    )
    book = models.ForeignKey(
        'narrative.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Which book this defeat occurred in. Null for mythological backstory.',
    )
    method = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='e.g. "Blinded with a sharpened stake", "Decapitated with Riptide"',
    )
    is_myth = models.BooleanField(
        default=False,
        help_text='True for mythological backstory defeats vs. series events.',
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Monster Defeat'
        verbose_name_plural = 'Monster Defeats'

    def __str__(self):
        return f'{self.defeated_by} defeated {self.monster}'


# ---------------------------------------------------------------------------
# Creature / Species
# ---------------------------------------------------------------------------


class Creature(BaseModel):
    """
    Species/type catalogue — not individual monsters but named creature types.

    e.g. Satyr, Centaur, Harpy, Fury, Cyclops, Pegasus.

    Typed member_records link named Characters or Monsters of this species;
    the notable_members manager remains Character-only for compatibility.
    abilities and weaknesses use JSONField per important-notes.md note 1.

    No image join table in V1 — species entries are reference data.
    Image support can be added in V2 if needed.
    """

    slug = AutoSlugField(populate_from='name', unique=True, editable=False)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    origin = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Greek mythological origin.',
    )
    alignment = models.CharField(
        max_length=20,
        choices=CREATURE_ALIGNMENT_CHOICES,
        default='neutral',
    )
    habitat = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='e.g. "forests", "sea", "Underworld"',
    )

    # JSONField per important-notes.md note 1
    abilities = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)

    # Character members remain available through the legacy M2M manager; typed
    # records additionally allow named Monsters to belong to a species.
    notable_members = models.ManyToManyField(
        'characters.Character',
        through='CreatureMember',
        through_fields=('creature', 'member_character'),
        blank=True,
        related_name='creature_species',
        help_text='Character members; use member_records for typed Character/Monster links.',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Creature / Species'
        verbose_name_plural = 'Creatures / Species'

    def __str__(self):
        return self.name


class CreatureMember(models.Model):
    """A typed link from a creature species to one Character or Monster."""

    creature = models.ForeignKey(Creature, on_delete=models.CASCADE, related_name='member_records')
    member_character = models.ForeignKey(
        'characters.Character',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='creature_member_links',
    )
    member_monster = models.ForeignKey(
        Monster,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='creature_member_links',
    )

    class Meta:
        ordering = ['id']
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(member_character__isnull=False, member_monster__isnull=True)
                    | models.Q(member_character__isnull=True, member_monster__isnull=False)
                ),
                name='creature_member_exactly_one_entity',
            ),
            models.UniqueConstraint(
                fields=('creature', 'member_character'),
                condition=models.Q(member_character__isnull=False),
                name='creature_member_unique_character',
            ),
            models.UniqueConstraint(
                fields=('creature', 'member_monster'),
                condition=models.Q(member_monster__isnull=False),
                name='creature_member_unique_monster',
            ),
        ]
        verbose_name = 'Creature Member'
        verbose_name_plural = 'Creature Members'

    def __str__(self):
        entity = self.member_character or self.member_monster
        return f'{self.creature}: {entity}'


# ---------------------------------------------------------------------------
# Image join table — Monster only
# ---------------------------------------------------------------------------


class MonsterImage(BaseImageLink):
    """Join table linking Monster to Image."""

    monster = models.ForeignKey(
        Monster,
        on_delete=models.CASCADE,
        related_name='images',
    )

    class Meta(BaseImageLink.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['monster'],
                condition=models.Q(is_primary=True),
                name='unique_primary_monster_image',
            )
        ]
        verbose_name = 'Monster Image'
        verbose_name_plural = 'Monster Images'
