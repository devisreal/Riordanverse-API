# ruff: noqa: RUF012
# ty: ignore[invalid-attribute-override]

from autoslug import AutoSlugField
from django.db import models

from apps.core.choices import (
    GOD_AFFILIATION_CHOICES,
    GOD_TIER_CHOICES,
    OATH_STATUS_CHOICES,
    STATUS_CHOICES,
    TITAN_ALIGNMENT_CHOICES,
    TITAN_GENERATION_CHOICES,
)
from apps.core.models import BaseModel
from apps.images.models import BaseImageLink

MYTHOLOGY_CHOICES = (
    ('greek', 'Greek'),
    ('roman', 'Roman'),
    ('egyptian', 'Egyptian'),
    ('norse', 'Norse'),
)

DIVINE_RELATIONSHIP_TYPE_CHOICES = (
    ('parent_of', 'Parent of'),
    ('sibling_of', 'Sibling of'),
    ('consort_of', 'Consort of'),
)

RELATIONSHIP_ENTITY_TYPES = ('god', 'titan', 'character', 'monster', 'creature')


# ---------------------------------------------------------------------------
# God
# ---------------------------------------------------------------------------


class God(BaseModel):
    """
    Covers all Olympians, minor gods, primordials, and chthonic deities.
    Titans are a separate model — see Titan below.

    Family relationships (parents, siblings, children, consorts) are
    modelled through DivineRelationship rather than direct M2M fields,
    so that cross-boundary relationships (e.g. God whose parent is a
    Titan) are handled cleanly.

    children_demigods is the one exception — it's a direct M2M to
    Character (string ref) since demigods are not Gods or Titans.
    """

    slug = AutoSlugField(populate_from='name', unique=True, editable=False)
    name = models.CharField(max_length=150)
    roman_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text='Roman equivalent name (e.g. Neptune for Poseidon).',
    )
    mythology = models.CharField(
        max_length=20,
        choices=MYTHOLOGY_CHOICES,
        default='greek',
        help_text='Mythology system this deity belongs to. Greek-only in V1.',
    )
    tier = models.CharField(
        max_length=20,
        choices=GOD_TIER_CHOICES,
        default='olympian',
    )
    affiliation = models.CharField(
        max_length=30,
        choices=GOD_AFFILIATION_CHOICES,
        default='olympian_council',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='immortal',
    )

    # Sacred attributes — JSONField per important-notes.md note 1
    domains = models.JSONField(
        default=list,
        help_text='["sky", "lightning", "thunder"]',
    )
    symbols = models.JSONField(default=list)
    sacred_animals = models.JSONField(default=list)
    sacred_plants = models.JSONField(default=list)
    sacred_items = models.JSONField(default=list)

    # Camp Half-Blood
    cabin_number = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text='CHB cabin number. Null if no cabin.',
    )
    has_cabin = models.BooleanField(default=False)
    is_big_three = models.BooleanField(
        default=False,
        help_text='True for Zeus, Poseidon, and Hades.',
    )

    # Big Three oath
    oath_status = models.CharField(
        max_length=20,
        choices=OATH_STATUS_CHOICES,
        default='not_applicable',
    )

    # Roman aspect (prepped for V2 dual-aspect system)
    greek_aspect_personality = models.TextField(blank=True, null=True)
    roman_aspect_personality = models.TextField(
        blank=True,
        null=True,
        help_text='Personality in Roman form. Populated in V2.',
    )

    # Flags
    roman_only = models.BooleanField(
        default=False,
        help_text='True for gods like Janus and Pomona who are purely Roman.',
    )

    # Demigod children — direct M2M to Character (string ref)
    children_demigods = models.ManyToManyField(
        'characters.Character',
        blank=True,
        related_name='divine_parent_god',
        help_text='Named demigod children.',
    )

    # Weapons/items associated — string ref to items app
    weapons = models.ManyToManyField(
        'items.Weapon',
        blank=True,
        related_name='associated_gods',
    )

    # Books
    first_appearance_book = models.ForeignKey(
        'narrative.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gods_first_appearing',
    )
    books_appeared_in = models.ManyToManyField(
        'narrative.Book',
        blank=True,
        related_name='gods',
    )

    home = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='e.g. "Mount Olympus", "The Underworld", "The Sea"',
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'God'
        verbose_name_plural = 'Gods'

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Titan
# ---------------------------------------------------------------------------


class Titan(BaseModel):
    """
    Predecessor deities — distinct from gods due to their unique role
    as antagonists and progenitors.

    Family relationships modelled through DivineRelationship.
    """

    slug = AutoSlugField(populate_from='name', unique=True, editable=False)
    name = models.CharField(max_length=150)
    roman_name = models.CharField(max_length=150, blank=True, null=True)
    mythology = models.CharField(
        max_length=20,
        choices=MYTHOLOGY_CHOICES,
        default='greek',
    )
    generation = models.CharField(
        max_length=20,
        choices=TITAN_GENERATION_CHOICES,
        default='elder_titan',
    )
    display_order = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Curated list order; independent of the Titan generation classification.',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='imprisoned',
    )
    alignment = models.CharField(
        max_length=20,
        choices=TITAN_ALIGNMENT_CHOICES,
        default='kronos_army',
    )

    # Sacred attributes and powers.
    domains = models.JSONField(default=list)
    symbols = models.JSONField(default=list)
    sacred_animals = models.JSONField(default=list)
    sacred_plants = models.JSONField(default=list)
    weapon_or_power = models.JSONField(
        default=list,
        help_text='Notable powers or items.',
    )
    weapons = models.ManyToManyField(
        'items.Weapon',
        blank=True,
        related_name='associated_titans',
    )

    home = models.CharField(max_length=255, blank=True, null=True)
    role_in_series = models.TextField(
        blank=True,
        null=True,
        help_text='Their narrative function in V1.',
    )
    prison_location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Where they are imprisoned, if applicable.',
    )

    # Books
    first_appearance_book = models.ForeignKey(
        'narrative.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='titans_first_appearing',
    )
    books_appeared_in = models.ManyToManyField(
        'narrative.Book',
        blank=True,
        related_name='titans',
    )

    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = [models.F('display_order').asc(nulls_last=True), 'name']
        verbose_name = 'Titan'
        verbose_name_plural = 'Titans'

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# DivineRelationship
# ---------------------------------------------------------------------------


class DivineRelationship(models.Model):
    """
    Directed graph edge representing a family relationship between Gods,
    Titans, Characters, Monsters, and Creatures.

    Each row has exactly one "from" entity and exactly one "to" entity,
    enforced by CheckConstraints. This allows cross-type relationships that
    simple M2M fields on individual entity models cannot express.

    The API consumer never sees the raw FK fields — serializers flatten
    them into a clean {type, slug, name} shape. See GodDetailSerializer
    for the pattern.

    mythology is stored on both God and Titan directly, not here.
    This table is relationship-only.
    """

    # "From" entity — exactly one must be set (enforced by CheckConstraint)
    from_god = models.ForeignKey(
        God,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='relationships_as_from',
    )
    from_titan = models.ForeignKey(
        Titan,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='relationships_as_from',
    )
    from_character = models.ForeignKey(
        'characters.Character',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='divine_relationships_as_from',
    )
    from_monster = models.ForeignKey(
        'bestiary.Monster',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='family_relationships_as_from',
    )
    from_creature = models.ForeignKey(
        'bestiary.Creature',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='family_relationships_as_from',
    )

    # "To" entity — exactly one must be set (enforced by CheckConstraint)
    to_god = models.ForeignKey(
        God,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='relationships_as_to',
    )
    to_titan = models.ForeignKey(
        Titan,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='relationships_as_to',
    )
    to_character = models.ForeignKey(
        'characters.Character',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='divine_relationships_as_to',
    )
    to_monster = models.ForeignKey(
        'bestiary.Monster',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='family_relationships_as_to',
    )
    to_creature = models.ForeignKey(
        'bestiary.Creature',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='family_relationships_as_to',
    )

    relationship_type = models.CharField(
        max_length=20,
        choices=DIVINE_RELATIONSHIP_TYPE_CHOICES,
    )

    class Meta:
        verbose_name = 'Divine Relationship'
        verbose_name_plural = 'Divine Relationships'
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        from_god__isnull=False,
                        from_titan__isnull=True,
                        from_character__isnull=True,
                        from_monster__isnull=True,
                        from_creature__isnull=True,
                    )
                    | models.Q(
                        from_god__isnull=True,
                        from_titan__isnull=False,
                        from_character__isnull=True,
                        from_monster__isnull=True,
                        from_creature__isnull=True,
                    )
                    | models.Q(
                        from_god__isnull=True,
                        from_titan__isnull=True,
                        from_character__isnull=False,
                        from_monster__isnull=True,
                        from_creature__isnull=True,
                    )
                    | models.Q(
                        from_god__isnull=True,
                        from_titan__isnull=True,
                        from_character__isnull=True,
                        from_monster__isnull=False,
                        from_creature__isnull=True,
                    )
                    | models.Q(
                        from_god__isnull=True,
                        from_titan__isnull=True,
                        from_character__isnull=True,
                        from_monster__isnull=True,
                        from_creature__isnull=False,
                    )
                ),
                name='divine_rel_exactly_one_from',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        to_god__isnull=False,
                        to_titan__isnull=True,
                        to_character__isnull=True,
                        to_monster__isnull=True,
                        to_creature__isnull=True,
                    )
                    | models.Q(
                        to_god__isnull=True,
                        to_titan__isnull=False,
                        to_character__isnull=True,
                        to_monster__isnull=True,
                        to_creature__isnull=True,
                    )
                    | models.Q(
                        to_god__isnull=True,
                        to_titan__isnull=True,
                        to_character__isnull=False,
                        to_monster__isnull=True,
                        to_creature__isnull=True,
                    )
                    | models.Q(
                        to_god__isnull=True,
                        to_titan__isnull=True,
                        to_character__isnull=True,
                        to_monster__isnull=False,
                        to_creature__isnull=True,
                    )
                    | models.Q(
                        to_god__isnull=True,
                        to_titan__isnull=True,
                        to_character__isnull=True,
                        to_monster__isnull=True,
                        to_creature__isnull=False,
                    )
                ),
                name='divine_rel_exactly_one_to',
            ),
            *[
                models.UniqueConstraint(
                    fields=[f'from_{source}', f'to_{target}', 'relationship_type'],
                    condition=models.Q(
                        **{
                            **{
                                f'from_{kind}__isnull': kind != source
                                for kind in RELATIONSHIP_ENTITY_TYPES
                            },
                            **{
                                f'to_{kind}__isnull': kind != target
                                for kind in RELATIONSHIP_ENTITY_TYPES
                            },
                        },
                    ),
                    name=f'unique_dr_{source}_{target}',
                )
                for source in RELATIONSHIP_ENTITY_TYPES
                for target in RELATIONSHIP_ENTITY_TYPES
            ],
        ]

    def __str__(self):
        from_entity = (
            self.from_god
            or self.from_titan
            or self.from_character
            or self.from_monster
            or self.from_creature
        )
        to_entity = (
            self.to_god or self.to_titan or self.to_character or self.to_monster or self.to_creature
        )
        return f'{from_entity} → {self.relationship_type} → {to_entity}'


# ---------------------------------------------------------------------------
# Image join tables
# ---------------------------------------------------------------------------


class GodImage(BaseImageLink):
    god = models.ForeignKey(God, on_delete=models.CASCADE, related_name='images')

    class Meta(BaseImageLink.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['god'],
                condition=models.Q(is_primary=True),
                name='unique_primary_god_image',
            )
        ]
        verbose_name = 'God Image'
        verbose_name_plural = 'God Images'


class TitanImage(BaseImageLink):
    titan = models.ForeignKey(Titan, on_delete=models.CASCADE, related_name='images')

    class Meta(BaseImageLink.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['titan'],
                condition=models.Q(is_primary=True),
                name='unique_primary_titan_image',
            )
        ]
        verbose_name = 'Titan Image'
        verbose_name_plural = 'Titan Images'
