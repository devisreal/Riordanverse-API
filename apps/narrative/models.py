from autoslug import AutoSlugField
from django.db import models

from apps.core.choices import BOOK_TYPE_CHOICES, EVENT_TYPE_CHOICES, SERIES_CHOICES
from apps.core.models import BaseModel
from apps.images.models import BaseImageLink


class Book(BaseModel):
    """A novel, companion work, or other book in the Riordanverse."""

    slug = AutoSlugField(populate_from='title', unique=True, editable=False)
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
    parent_collection = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='included_stories',
        help_text='Parent anthology or collection for an individual short story.',
    )

    narrator = models.ForeignKey(
        'characters.Character',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='narrated_books',
        help_text='Percy Jackson for all PJO books.',
    )
    narrators = models.ManyToManyField(
        'characters.Character',
        through='BookNarrator',
        through_fields=('book', 'character'),
        blank=True,
        related_name='books_as_narrator',
        help_text='Character narrators; typed narrator links are in narrator_records.',
    )
    main_characters = models.ManyToManyField(
        'characters.Character',
        through='BookMainCharacter',
        through_fields=('book', 'character'),
        blank=True,
        related_name='books_as_main_character',
        help_text='Character main links; typed main-character links are in main_character_records.',
    )
    antagonists = models.ManyToManyField(
        'characters.Character',
        through='BookAntagonist',
        through_fields=('book', 'character'),
        blank=True,
        related_name='books_as_antagonist',
        help_text='Character antagonist links; typed links are in antagonist_records.',
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


class BookNarrator(models.Model):
    """A typed narrator link from a Book to exactly one lore entity."""

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='narrator_records')
    character = models.ForeignKey(
        'characters.Character',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_narrator_links',
    )
    god = models.ForeignKey(
        'divinities.God',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_narrator_links',
    )
    titan = models.ForeignKey(
        'divinities.Titan',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_narrator_links',
    )
    monster = models.ForeignKey(
        'bestiary.Monster',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_narrator_links',
    )
    creature = models.ForeignKey(
        'bestiary.Creature',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_narrator_links',
    )

    class Meta:
        ordering = ['id']  # noqa: RUF012
        constraints = (
            models.CheckConstraint(
                condition=(
                    models.Q(
                        character__isnull=False,
                        god__isnull=True,
                        titan__isnull=True,
                        monster__isnull=True,
                        creature__isnull=True,
                    )
                    | models.Q(
                        character__isnull=True,
                        god__isnull=False,
                        titan__isnull=True,
                        monster__isnull=True,
                        creature__isnull=True,
                    )
                    | models.Q(
                        character__isnull=True,
                        god__isnull=True,
                        titan__isnull=False,
                        monster__isnull=True,
                        creature__isnull=True,
                    )
                    | models.Q(
                        character__isnull=True,
                        god__isnull=True,
                        titan__isnull=True,
                        monster__isnull=False,
                        creature__isnull=True,
                    )
                    | models.Q(
                        character__isnull=True,
                        god__isnull=True,
                        titan__isnull=True,
                        monster__isnull=True,
                        creature__isnull=False,
                    )
                ),
                name='book_narrator_exactly_one_entity',
            ),
            models.UniqueConstraint(
                fields=('book', 'character'),
                condition=models.Q(character__isnull=False),
                name='book_narrator_unique_character',
            ),
            models.UniqueConstraint(
                fields=('book', 'god'),
                condition=models.Q(god__isnull=False),
                name='book_narrator_unique_god',
            ),
            models.UniqueConstraint(
                fields=('book', 'titan'),
                condition=models.Q(titan__isnull=False),
                name='book_narrator_unique_titan',
            ),
            models.UniqueConstraint(
                fields=('book', 'monster'),
                condition=models.Q(monster__isnull=False),
                name='book_narrator_unique_monster',
            ),
            models.UniqueConstraint(
                fields=('book', 'creature'),
                condition=models.Q(creature__isnull=False),
                name='book_narrator_unique_creature',
            ),
        )
        verbose_name = 'Book Narrator'
        verbose_name_plural = 'Book Narrators'

    def __str__(self):
        entity = self.character or self.god or self.titan or self.monster or self.creature
        return f'{self.book}: {entity}'


class BookMainCharacter(models.Model):
    """A typed main-character link from a Book to exactly one lore entity."""

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='main_character_records')
    character = models.ForeignKey(
        'characters.Character',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_main_character_links',
    )
    god = models.ForeignKey(
        'divinities.God',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_main_character_links',
    )
    titan = models.ForeignKey(
        'divinities.Titan',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_main_character_links',
    )
    monster = models.ForeignKey(
        'bestiary.Monster',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_main_character_links',
    )
    creature = models.ForeignKey(
        'bestiary.Creature',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_main_character_links',
    )

    class Meta:
        ordering = ['id']  # noqa: RUF012
        constraints = (
            models.CheckConstraint(
                condition=(
                    models.Q(
                        character__isnull=False,
                        god__isnull=True,
                        titan__isnull=True,
                        monster__isnull=True,
                        creature__isnull=True,
                    )
                    | models.Q(
                        character__isnull=True,
                        god__isnull=False,
                        titan__isnull=True,
                        monster__isnull=True,
                        creature__isnull=True,
                    )
                    | models.Q(
                        character__isnull=True,
                        god__isnull=True,
                        titan__isnull=False,
                        monster__isnull=True,
                        creature__isnull=True,
                    )
                    | models.Q(
                        character__isnull=True,
                        god__isnull=True,
                        titan__isnull=True,
                        monster__isnull=False,
                        creature__isnull=True,
                    )
                    | models.Q(
                        character__isnull=True,
                        god__isnull=True,
                        titan__isnull=True,
                        monster__isnull=True,
                        creature__isnull=False,
                    )
                ),
                name='book_main_character_exactly_one_entity',
            ),
            models.UniqueConstraint(
                fields=('book', 'character'),
                condition=models.Q(character__isnull=False),
                name='book_main_character_unique_character',
            ),
            models.UniqueConstraint(
                fields=('book', 'god'),
                condition=models.Q(god__isnull=False),
                name='book_main_character_unique_god',
            ),
            models.UniqueConstraint(
                fields=('book', 'titan'),
                condition=models.Q(titan__isnull=False),
                name='book_main_character_unique_titan',
            ),
            models.UniqueConstraint(
                fields=('book', 'monster'),
                condition=models.Q(monster__isnull=False),
                name='book_main_character_unique_monster',
            ),
            models.UniqueConstraint(
                fields=('book', 'creature'),
                condition=models.Q(creature__isnull=False),
                name='book_main_character_unique_creature',
            ),
        )
        verbose_name = 'Book Main Character'
        verbose_name_plural = 'Book Main Characters'

    def __str__(self):
        entity = self.character or self.god or self.titan or self.monster or self.creature
        return f'{self.book}: {entity}'


class BookAntagonist(models.Model):
    """A typed antagonist link from a Book to exactly one lore entity."""

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='antagonist_records')
    character = models.ForeignKey(
        'characters.Character',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_antagonist_links',
    )
    god = models.ForeignKey(
        'divinities.God',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_antagonist_links',
    )
    titan = models.ForeignKey(
        'divinities.Titan',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_antagonist_links',
    )
    monster = models.ForeignKey(
        'bestiary.Monster',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_antagonist_links',
    )
    creature = models.ForeignKey(
        'bestiary.Creature',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='book_antagonist_links',
    )

    class Meta:
        ordering = ['id']  # noqa: RUF012
        constraints = (
            models.CheckConstraint(
                condition=(
                    models.Q(
                        character__isnull=False,
                        god__isnull=True,
                        titan__isnull=True,
                        monster__isnull=True,
                        creature__isnull=True,
                    )
                    | models.Q(
                        character__isnull=True,
                        god__isnull=False,
                        titan__isnull=True,
                        monster__isnull=True,
                        creature__isnull=True,
                    )
                    | models.Q(
                        character__isnull=True,
                        god__isnull=True,
                        titan__isnull=False,
                        monster__isnull=True,
                        creature__isnull=True,
                    )
                    | models.Q(
                        character__isnull=True,
                        god__isnull=True,
                        titan__isnull=True,
                        monster__isnull=False,
                        creature__isnull=True,
                    )
                    | models.Q(
                        character__isnull=True,
                        god__isnull=True,
                        titan__isnull=True,
                        monster__isnull=True,
                        creature__isnull=False,
                    )
                ),
                name='book_antagonist_exactly_one_entity',
            ),
            models.UniqueConstraint(
                fields=('book', 'character'),
                condition=models.Q(character__isnull=False),
                name='book_antagonist_unique_character',
            ),
            models.UniqueConstraint(
                fields=('book', 'god'),
                condition=models.Q(god__isnull=False),
                name='book_antagonist_unique_god',
            ),
            models.UniqueConstraint(
                fields=('book', 'titan'),
                condition=models.Q(titan__isnull=False),
                name='book_antagonist_unique_titan',
            ),
            models.UniqueConstraint(
                fields=('book', 'monster'),
                condition=models.Q(monster__isnull=False),
                name='book_antagonist_unique_monster',
            ),
            models.UniqueConstraint(
                fields=('book', 'creature'),
                condition=models.Q(creature__isnull=False),
                name='book_antagonist_unique_creature',
            ),
        )
        verbose_name = 'Book Antagonist'
        verbose_name_plural = 'Book Antagonists'

    def __str__(self):
        entity = self.character or self.god or self.titan or self.monster or self.creature
        return f'{self.book}: {entity}'


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


# ---------------------------------------------------------------------------
# Prophecy
# ---------------------------------------------------------------------------


class Prophecy(BaseModel):
    """
    An Oracle prophecy from the series.

    text is stored as a plain TextField with natural newlines.
    The serializer returns both:
    - text: the raw string (for storage, admin, and completeness)
    - prophecy_lines: text split by newline into a list (for frontend rendering)

    This avoids any client-side string splitting while keeping the Admin
    experience natural — just type the prophecy with line breaks.
    """

    slug = AutoSlugField(populate_from='title', unique=True, editable=False)
    title = models.CharField(
        max_length=255,
        help_text='e.g. "The Great Prophecy"',
    )
    text = models.TextField(
        help_text=(
            'Full prophecy text. Use natural line breaks — the API will '
            'return both the raw text and a split list via prophecy_lines.'
        ),
    )
    oracle_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='e.g. "Oracle of Delphi"',
    )
    delivered_by = models.ForeignKey(
        'characters.Character',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prophecies_delivered',
        help_text='The Oracle or character who delivered this prophecy.',
    )
    subject = models.ManyToManyField(
        'characters.Character',
        through='ProphecySubject',
        through_fields=('prophecy', 'subject_character'),
        blank=True,
        related_name='prophecies_about',
        help_text='Character subjects; typed subjects are represented by ProphecySubject.',
    )
    fulfilled_in = models.ForeignKey(
        'narrative.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prophecies_fulfilled',
        help_text='Book in which this prophecy was fulfilled.',
    )
    books_relevant_to = models.ManyToManyField(
        'narrative.Book',
        blank=True,
        related_name='prophecies',
    )
    interpretation_notes = models.TextField(
        blank=True,
        null=True,
        help_text='How the prophecy was ultimately interpreted and fulfilled.',
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['title']  # noqa: RUF012
        verbose_name = 'Prophecy'
        verbose_name_plural = 'Prophecies'

    def __str__(self):
        return self.title


class ProphecySubject(models.Model):
    """A typed subject link from a Prophecy to exactly one lore entity."""

    prophecy = models.ForeignKey(
        Prophecy,
        on_delete=models.CASCADE,
        related_name='subject_records',
    )
    subject_character = models.ForeignKey(
        'characters.Character',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='prophecy_subject_links',
    )
    subject_god = models.ForeignKey(
        'divinities.God',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='prophecy_subject_links',
    )
    subject_titan = models.ForeignKey(
        'divinities.Titan',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='prophecy_subject_links',
    )
    subject_monster = models.ForeignKey(
        'bestiary.Monster',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='prophecy_subject_links',
    )

    class Meta:
        ordering = ['id']  # noqa: RUF012
        constraints = (
            models.CheckConstraint(
                condition=(
                    models.Q(
                        subject_character__isnull=False,
                        subject_god__isnull=True,
                        subject_titan__isnull=True,
                        subject_monster__isnull=True,
                    )
                    | models.Q(
                        subject_character__isnull=True,
                        subject_god__isnull=False,
                        subject_titan__isnull=True,
                        subject_monster__isnull=True,
                    )
                    | models.Q(
                        subject_character__isnull=True,
                        subject_god__isnull=True,
                        subject_titan__isnull=False,
                        subject_monster__isnull=True,
                    )
                    | models.Q(
                        subject_character__isnull=True,
                        subject_god__isnull=True,
                        subject_titan__isnull=True,
                        subject_monster__isnull=False,
                    )
                ),
                name='prophecy_subject_exactly_one_entity',
            ),
            models.UniqueConstraint(
                fields=('prophecy', 'subject_character'),
                condition=models.Q(subject_character__isnull=False),
                name='prophecy_subject_unique_character',
            ),
            models.UniqueConstraint(
                fields=('prophecy', 'subject_god'),
                condition=models.Q(subject_god__isnull=False),
                name='prophecy_subject_unique_god',
            ),
            models.UniqueConstraint(
                fields=('prophecy', 'subject_titan'),
                condition=models.Q(subject_titan__isnull=False),
                name='prophecy_subject_unique_titan',
            ),
            models.UniqueConstraint(
                fields=('prophecy', 'subject_monster'),
                condition=models.Q(subject_monster__isnull=False),
                name='prophecy_subject_unique_monster',
            ),
        )
        verbose_name = 'Prophecy Subject'
        verbose_name_plural = 'Prophecy Subjects'

    def __str__(self):
        entity = (
            self.subject_character or self.subject_god or self.subject_titan or self.subject_monster
        )
        return f'{self.prophecy}: {entity}'


# ---------------------------------------------------------------------------
# Quest
# ---------------------------------------------------------------------------


class Quest(BaseModel):
    """
    A named quest undertaken in V1.

    prophecy is a OneToOneField to Prophecy. Both models are defined in
    the same app, so Django resolves this within the same migration.

    casualties tracks characters who died during this quest specifically,
    separate from their overall status field on Character.
    """

    slug = AutoSlugField(populate_from='title', unique=True, editable=False)
    title = models.CharField(
        max_length=255,
        help_text='e.g. "The Quest for Zeus\'s Lightning Bolt"',
    )
    book = models.ForeignKey(
        'narrative.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quests',
    )
    prophecy = models.OneToOneField(
        Prophecy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quest',
        help_text='The Oracle prophecy that initiated this quest.',
    )
    led_by = models.ForeignKey(
        'characters.Character',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quests_led',
    )
    participants = models.ManyToManyField(
        'characters.Character',
        through='QuestParticipant',
        through_fields=('quest', 'participant_character'),
        blank=True,
        related_name='quests_participated_in',
        help_text='Character participants; typed participant records support all entity types.',
    )
    objective = models.TextField(
        blank=True,
        null=True,
        help_text='What the quest is trying to achieve.',
    )
    outcome = models.TextField(
        blank=True,
        null=True,
        help_text='What actually happened.',
    )
    initiated_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Who or what started the quest e.g. "Oracle of Delphi".',
    )
    locations_visited = models.ManyToManyField(
        'locations.Location',
        blank=True,
        related_name='quests_visited',
    )
    monsters_encountered = models.ManyToManyField(
        'bestiary.Monster',
        blank=True,
        related_name='quests_encountered_in',
    )
    items_recovered = models.ManyToManyField(
        'items.Weapon',
        blank=True,
        related_name='quests_recovered_in',
        help_text='Magical items found or returned during this quest.',
    )
    casualties = models.ManyToManyField(
        'characters.Character',
        through='QuestCasualty',
        through_fields=('quest', 'casualty_character'),
        blank=True,
        related_name='quests_died_in',
        help_text='Character casualties; typed casualty records support all entity types.',
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['book__book_number', 'title']  # noqa: RUF012
        verbose_name = 'Quest'
        verbose_name_plural = 'Quests'

    def __str__(self):
        return self.title


class QuestParticipant(models.Model):
    """A typed participant link from a Quest to exactly one lore entity."""

    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='participant_records')
    participant_character = models.ForeignKey(
        'characters.Character',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quest_participant_links',
    )
    participant_god = models.ForeignKey(
        'divinities.God',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quest_participant_links',
    )
    participant_titan = models.ForeignKey(
        'divinities.Titan',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quest_participant_links',
    )
    participant_monster = models.ForeignKey(
        'bestiary.Monster',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quest_participant_links',
    )

    class Meta:
        ordering = ['id']  # noqa: RUF012
        constraints = (
            models.CheckConstraint(
                condition=(
                    models.Q(
                        participant_character__isnull=False,
                        participant_god__isnull=True,
                        participant_titan__isnull=True,
                        participant_monster__isnull=True,
                    )
                    | models.Q(
                        participant_character__isnull=True,
                        participant_god__isnull=False,
                        participant_titan__isnull=True,
                        participant_monster__isnull=True,
                    )
                    | models.Q(
                        participant_character__isnull=True,
                        participant_god__isnull=True,
                        participant_titan__isnull=False,
                        participant_monster__isnull=True,
                    )
                    | models.Q(
                        participant_character__isnull=True,
                        participant_god__isnull=True,
                        participant_titan__isnull=True,
                        participant_monster__isnull=False,
                    )
                ),
                name='quest_participant_exactly_one_entity',
            ),
            models.UniqueConstraint(
                fields=('quest', 'participant_character'),
                condition=models.Q(participant_character__isnull=False),
                name='quest_participant_unique_character',
            ),
            models.UniqueConstraint(
                fields=('quest', 'participant_god'),
                condition=models.Q(participant_god__isnull=False),
                name='quest_participant_unique_god',
            ),
            models.UniqueConstraint(
                fields=('quest', 'participant_titan'),
                condition=models.Q(participant_titan__isnull=False),
                name='quest_participant_unique_titan',
            ),
            models.UniqueConstraint(
                fields=('quest', 'participant_monster'),
                condition=models.Q(participant_monster__isnull=False),
                name='quest_participant_unique_monster',
            ),
        )
        verbose_name = 'Quest Participant'
        verbose_name_plural = 'Quest Participants'

    def __str__(self):
        entity = (
            self.participant_character
            or self.participant_god
            or self.participant_titan
            or self.participant_monster
        )
        return f'{self.quest}: {entity}'


class QuestCasualty(models.Model):
    """A typed casualty link from a Quest to exactly one lore entity."""

    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='casualty_records')
    casualty_character = models.ForeignKey(
        'characters.Character',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quest_casualty_links',
    )
    casualty_god = models.ForeignKey(
        'divinities.God',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quest_casualty_links',
    )
    casualty_titan = models.ForeignKey(
        'divinities.Titan',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quest_casualty_links',
    )
    casualty_monster = models.ForeignKey(
        'bestiary.Monster',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quest_casualty_links',
    )

    class Meta:
        ordering = ['id']  # noqa: RUF012
        constraints = (
            models.CheckConstraint(
                condition=(
                    models.Q(
                        casualty_character__isnull=False,
                        casualty_god__isnull=True,
                        casualty_titan__isnull=True,
                        casualty_monster__isnull=True,
                    )
                    | models.Q(
                        casualty_character__isnull=True,
                        casualty_god__isnull=False,
                        casualty_titan__isnull=True,
                        casualty_monster__isnull=True,
                    )
                    | models.Q(
                        casualty_character__isnull=True,
                        casualty_god__isnull=True,
                        casualty_titan__isnull=False,
                        casualty_monster__isnull=True,
                    )
                    | models.Q(
                        casualty_character__isnull=True,
                        casualty_god__isnull=True,
                        casualty_titan__isnull=True,
                        casualty_monster__isnull=False,
                    )
                ),
                name='quest_casualty_exactly_one_entity',
            ),
            models.UniqueConstraint(
                fields=('quest', 'casualty_character'),
                condition=models.Q(casualty_character__isnull=False),
                name='quest_casualty_unique_character',
            ),
            models.UniqueConstraint(
                fields=('quest', 'casualty_god'),
                condition=models.Q(casualty_god__isnull=False),
                name='quest_casualty_unique_god',
            ),
            models.UniqueConstraint(
                fields=('quest', 'casualty_titan'),
                condition=models.Q(casualty_titan__isnull=False),
                name='quest_casualty_unique_titan',
            ),
            models.UniqueConstraint(
                fields=('quest', 'casualty_monster'),
                condition=models.Q(casualty_monster__isnull=False),
                name='quest_casualty_unique_monster',
            ),
        )
        verbose_name = 'Quest Casualty'
        verbose_name_plural = 'Quest Casualties'

    def __str__(self):
        entity = (
            self.casualty_character
            or self.casualty_god
            or self.casualty_titan
            or self.casualty_monster
        )
        return f'{self.quest}: {entity}'


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------


class Event(BaseModel):
    """
    A named battle or significant event in the lore.

    Participants are split into four separate M2M fields (Option A) —
    one per entity type — rather than JSONField slugs. This keeps them
    queryable and consistent with the rest of the data model.

    participant_monsters was added beyond API.md's original spec to
    cover events like the Battle of Manhattan where named monsters
    (Lydian Drakon, Typhon) are key participants.
    """

    slug = AutoSlugField(populate_from='name', unique=True, editable=False)
    name = models.CharField(max_length=255)
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        default='battle',
        db_column='type',
    )
    book = models.ForeignKey(
        'narrative.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
    )
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
    )

    # Participants — four separate M2M fields (Option A, confirmed)
    participant_characters = models.ManyToManyField(
        'characters.Character',
        blank=True,
        related_name='events_participated_in',
    )
    participant_gods = models.ManyToManyField(
        'divinities.God',
        blank=True,
        related_name='events_participated_in',
    )
    participant_titans = models.ManyToManyField(
        'divinities.Titan',
        blank=True,
        related_name='events_participated_in',
    )
    participant_monsters = models.ManyToManyField(
        'bestiary.Monster',
        blank=True,
        related_name='events_participated_in',
        help_text='Named monsters participating in this event (extension beyond API.md spec).',
    )

    casualties = models.ManyToManyField(
        'characters.Character',
        through='EventCasualty',
        through_fields=('event', 'casualty_character'),
        blank=True,
        related_name='events_died_in',
        help_text='Character casualties; typed casualty records support all entity types.',
    )
    outcome = models.TextField(blank=True, null=True)
    significance = models.TextField(
        blank=True,
        null=True,
        help_text='Why this event matters in the lore.',
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['book__book_number', 'name']  # noqa: RUF012
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        return self.name


class EventCasualty(models.Model):
    """A typed casualty link from an Event to exactly one lore entity."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='casualty_records')
    casualty_character = models.ForeignKey(
        'characters.Character',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='event_casualty_links',
    )
    casualty_god = models.ForeignKey(
        'divinities.God',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='event_casualty_links',
    )
    casualty_titan = models.ForeignKey(
        'divinities.Titan',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='event_casualty_links',
    )
    casualty_monster = models.ForeignKey(
        'bestiary.Monster',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='event_casualty_links',
    )

    class Meta:
        ordering = ['id']  # noqa: RUF012
        constraints = (
            models.CheckConstraint(
                condition=(
                    models.Q(
                        casualty_character__isnull=False,
                        casualty_god__isnull=True,
                        casualty_titan__isnull=True,
                        casualty_monster__isnull=True,
                    )
                    | models.Q(
                        casualty_character__isnull=True,
                        casualty_god__isnull=False,
                        casualty_titan__isnull=True,
                        casualty_monster__isnull=True,
                    )
                    | models.Q(
                        casualty_character__isnull=True,
                        casualty_god__isnull=True,
                        casualty_titan__isnull=False,
                        casualty_monster__isnull=True,
                    )
                    | models.Q(
                        casualty_character__isnull=True,
                        casualty_god__isnull=True,
                        casualty_titan__isnull=True,
                        casualty_monster__isnull=False,
                    )
                ),
                name='event_casualty_exactly_one_entity',
            ),
            models.UniqueConstraint(
                fields=('event', 'casualty_character'),
                condition=models.Q(casualty_character__isnull=False),
                name='event_casualty_unique_character',
            ),
            models.UniqueConstraint(
                fields=('event', 'casualty_god'),
                condition=models.Q(casualty_god__isnull=False),
                name='event_casualty_unique_god',
            ),
            models.UniqueConstraint(
                fields=('event', 'casualty_titan'),
                condition=models.Q(casualty_titan__isnull=False),
                name='event_casualty_unique_titan',
            ),
            models.UniqueConstraint(
                fields=('event', 'casualty_monster'),
                condition=models.Q(casualty_monster__isnull=False),
                name='event_casualty_unique_monster',
            ),
        )
        verbose_name = 'Event Casualty'
        verbose_name_plural = 'Event Casualties'

    def __str__(self):
        entity = (
            self.casualty_character
            or self.casualty_god
            or self.casualty_titan
            or self.casualty_monster
        )
        return f'{self.event}: {entity}'
