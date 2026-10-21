from rest_framework import serializers

from apps.images.serializers import ImageListSerializer
from apps.narrative.models import (
    Book,
    Event,
    Prophecy,
    ProphecySubject,
    Quest,
    QuestCasualty,
    QuestParticipant,
)


def get_primary_image(book):
    link = next((image_link for image_link in book.images.all() if image_link.is_primary), None)
    return ImageListSerializer(link.image).data if link else None


class BookSummarySerializer(serializers.ModelSerializer):
    """Compact reference used for parent and included-story relationships."""

    class Meta:
        model = Book
        fields = ('id', 'slug', 'title', 'book_type', 'published_date')


class BookListSerializer(serializers.ModelSerializer):
    """Lightweight representation for book collection responses."""

    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = (
            'id',
            'slug',
            'title',
            'series',
            'book_number',
            'book_type',
            'published_date',
            'short_description',
            'camp_bead_description',
            'primary_image',
        )

    def get_primary_image(self, obj):
        return get_primary_image(obj)


class BookDetailSerializer(serializers.ModelSerializer):
    """Full representation for a single book."""

    primary_image = serializers.SerializerMethodField()
    narrator_slug = serializers.SerializerMethodField()
    main_character_slugs = serializers.SerializerMethodField()
    antagonist_slugs = serializers.SerializerMethodField()
    quest_count = serializers.SerializerMethodField()
    event_count = serializers.SerializerMethodField()
    series_display = serializers.CharField(source='get_series_display', read_only=True)
    book_type_display = serializers.CharField(source='get_book_type_display', read_only=True)
    parent_collection = BookSummarySerializer(read_only=True)
    included_stories = BookSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = (
            'id',
            'slug',
            'title',
            'series',
            'series_display',
            'book_number',
            'book_type',
            'book_type_display',
            'published_date',
            'parent_collection',
            'included_stories',
            'synopsis',
            'short_description',
            'camp_bead_description',
            'narrator_slug',
            'main_character_slugs',
            'antagonist_slugs',
            'quest_count',
            'event_count',
            'primary_image',
            'wiki_url',
            'created_at',
            'updated_at',
        )

    def get_primary_image(self, obj):
        return get_primary_image(obj)

    def get_narrator_slug(self, obj):
        return obj.narrator.slug if obj.narrator else None

    def get_main_character_slugs(self, obj):
        return list(obj.main_characters.values_list('slug', flat=True))

    def get_antagonist_slugs(self, obj):
        return list(obj.antagonists.values_list('slug', flat=True))

    def get_quest_count(self, obj):
        return obj.quests.count()

    def get_event_count(self, obj):
        return obj.events.count()


# ---------------------------------------------------------------------------
# Prophecy
# ---------------------------------------------------------------------------


class ProphecyListSerializer(serializers.ModelSerializer):
    """Lightweight — for list views."""

    delivered_by_slug = serializers.SerializerMethodField()
    fulfilled_in_slug = serializers.SerializerMethodField()
    prophecy_lines = serializers.SerializerMethodField()

    class Meta:
        model = Prophecy
        fields = (
            'id',
            'slug',
            'title',
            'oracle_type',
            'delivered_by_slug',
            'fulfilled_in_slug',
            'prophecy_lines',
        )

    def get_delivered_by_slug(self, obj):
        return obj.delivered_by.slug if obj.delivered_by else None

    def get_fulfilled_in_slug(self, obj):
        return obj.fulfilled_in.slug if obj.fulfilled_in else None

    def get_prophecy_lines(self, obj):
        if obj.text:
            return [line.strip() for line in obj.text.splitlines() if line.strip()]
        return []


class ProphecySubjectSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = ProphecySubject
        fields = ('type', 'slug', 'name')

    def _entity(self, obj):
        return obj.subject_character or obj.subject_god or obj.subject_titan or obj.subject_monster

    def get_type(self, obj):
        for subject_type in ('character', 'god', 'titan', 'monster'):
            if getattr(obj, f'subject_{subject_type}'):
                return subject_type
        return None

    def get_slug(self, obj):
        entity = self._entity(obj)
        return entity.slug if entity else None

    def get_name(self, obj):
        entity = self._entity(obj)
        return entity.name if entity else None


class ProphecyDetailSerializer(serializers.ModelSerializer):
    """Full detail — returns both raw text and split prophecy_lines."""

    delivered_by_slug = serializers.SerializerMethodField()
    fulfilled_in_slug = serializers.SerializerMethodField()
    subjects = ProphecySubjectSerializer(source='subject_records', many=True, read_only=True)
    subject_slugs = serializers.SerializerMethodField()
    books_relevant_to_slugs = serializers.SerializerMethodField()
    prophecy_lines = serializers.SerializerMethodField()

    class Meta:
        model = Prophecy
        fields = (
            'id',
            'slug',
            'title',
            'text',
            'prophecy_lines',
            'oracle_type',
            'delivered_by_slug',
            'subjects',
            'subject_slugs',
            'fulfilled_in_slug',
            'books_relevant_to_slugs',
            'interpretation_notes',
            'description',
            'wiki_url',
            'created_at',
            'updated_at',
        )

    def get_delivered_by_slug(self, obj):
        return obj.delivered_by.slug if obj.delivered_by else None

    def get_fulfilled_in_slug(self, obj):
        return obj.fulfilled_in.slug if obj.fulfilled_in else None

    def get_subject_slugs(self, obj):
        return list(obj.subject.values_list('slug', flat=True))

    def get_books_relevant_to_slugs(self, obj):
        return list(obj.books_relevant_to.values_list('slug', flat=True))

    def get_prophecy_lines(self, obj):
        if obj.text:
            return [line.strip() for line in obj.text.splitlines() if line.strip()]
        return []


# ---------------------------------------------------------------------------
# Quest
# ---------------------------------------------------------------------------


class QuestListSerializer(serializers.ModelSerializer):
    """Lightweight — for list views."""

    book_slug = serializers.SerializerMethodField()
    led_by_slug = serializers.SerializerMethodField()

    class Meta:
        model = Quest
        fields = (
            'id',
            'slug',
            'title',
            'book_slug',
            'led_by_slug',
            'initiated_by',
            'objective',
        )

    def get_book_slug(self, obj):
        return obj.book.slug if obj.book else None

    def get_led_by_slug(self, obj):
        return obj.led_by.slug if obj.led_by else None


class QuestParticipantSerializer(serializers.ModelSerializer):
    """Typed quest participant with a stable entity type, slug, and display name."""

    type = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = QuestParticipant
        fields = ('type', 'slug', 'name')

    def _entity(self, obj):
        for entity_type in ('character', 'god', 'titan', 'monster'):
            entity = getattr(obj, f'participant_{entity_type}')
            if entity:
                return entity_type, entity
        return None, None

    def get_type(self, obj):
        return self._entity(obj)[0]

    def get_slug(self, obj):
        return self._entity(obj)[1].slug

    def get_name(self, obj):
        return self._entity(obj)[1].name


class QuestCasualtySerializer(serializers.ModelSerializer):
    """Typed quest casualty with a stable entity type, slug, and display name."""

    type = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = QuestCasualty
        fields = ('type', 'slug', 'name')

    def _entity(self, obj):
        for entity_type in ('character', 'god', 'titan', 'monster'):
            entity = getattr(obj, f'casualty_{entity_type}')
            if entity:
                return entity_type, entity
        return None, None

    def get_type(self, obj):
        return self._entity(obj)[0]

    def get_slug(self, obj):
        return self._entity(obj)[1].slug

    def get_name(self, obj):
        return self._entity(obj)[1].name


class QuestDetailSerializer(serializers.ModelSerializer):
    """Full detail."""

    participants = QuestParticipantSerializer(
        source='participant_records', many=True, read_only=True
    )
    casualties = QuestCasualtySerializer(source='casualty_records', many=True, read_only=True)
    book_slug = serializers.SerializerMethodField()
    led_by_slug = serializers.SerializerMethodField()
    prophecy_slug = serializers.SerializerMethodField()
    participant_slugs = serializers.SerializerMethodField()
    casualty_slugs = serializers.SerializerMethodField()
    location_slugs = serializers.SerializerMethodField()
    monster_slugs = serializers.SerializerMethodField()
    item_slugs = serializers.SerializerMethodField()

    class Meta:
        model = Quest
        fields = (
            'id',
            'slug',
            'title',
            'book_slug',
            'prophecy_slug',
            'led_by_slug',
            'participants',
            'participant_slugs',
            'objective',
            'outcome',
            'initiated_by',
            'location_slugs',
            'monster_slugs',
            'item_slugs',
            'casualties',
            'casualty_slugs',
            'description',
            'wiki_url',
            'created_at',
            'updated_at',
        )

    def get_book_slug(self, obj):
        return obj.book.slug if obj.book else None

    def get_led_by_slug(self, obj):
        return obj.led_by.slug if obj.led_by else None

    def get_prophecy_slug(self, obj):
        return obj.prophecy.slug if obj.prophecy else None

    def get_participant_slugs(self, obj):
        return list(obj.participants.values_list('slug', flat=True))

    def get_casualty_slugs(self, obj):
        return list(obj.casualties.values_list('slug', flat=True))

    def get_location_slugs(self, obj):
        return list(obj.locations_visited.values_list('slug', flat=True))

    def get_monster_slugs(self, obj):
        return list(obj.monsters_encountered.values_list('slug', flat=True))

    def get_item_slugs(self, obj):
        return list(obj.items_recovered.values_list('slug', flat=True))


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------


class EventListSerializer(serializers.ModelSerializer):
    """Lightweight — for list views."""

    book_slug = serializers.SerializerMethodField()
    location_slug = serializers.SerializerMethodField()
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = Event
        fields = (
            'id',
            'slug',
            'name',
            'event_type',
            'event_type_display',
            'book_slug',
            'location_slug',
            'significance',
        )

    def get_book_slug(self, obj):
        return obj.book.slug if obj.book else None

    def get_location_slug(self, obj):
        return obj.location.slug if obj.location else None


class EventDetailSerializer(serializers.ModelSerializer):
    """Full detail."""

    book_slug = serializers.SerializerMethodField()
    location_slug = serializers.SerializerMethodField()
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    participant_character_slugs = serializers.SerializerMethodField()
    participant_god_slugs = serializers.SerializerMethodField()
    participant_titan_slugs = serializers.SerializerMethodField()
    participant_monster_slugs = serializers.SerializerMethodField()
    casualty_slugs = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            'id',
            'slug',
            'name',
            'event_type',
            'event_type_display',
            'book_slug',
            'location_slug',
            'participant_character_slugs',
            'participant_god_slugs',
            'participant_titan_slugs',
            'participant_monster_slugs',
            'casualty_slugs',
            'outcome',
            'significance',
            'description',
            'wiki_url',
            'created_at',
            'updated_at',
        )

    def get_book_slug(self, obj):
        return obj.book.slug if obj.book else None

    def get_location_slug(self, obj):
        return obj.location.slug if obj.location else None

    def get_participant_character_slugs(self, obj):
        return list(obj.participant_characters.values_list('slug', flat=True))

    def get_participant_god_slugs(self, obj):
        return list(obj.participant_gods.values_list('slug', flat=True))

    def get_participant_titan_slugs(self, obj):
        return list(obj.participant_titans.values_list('slug', flat=True))

    def get_participant_monster_slugs(self, obj):
        return list(obj.participant_monsters.values_list('slug', flat=True))

    def get_casualty_slugs(self, obj):
        return list(obj.casualties.values_list('slug', flat=True))
