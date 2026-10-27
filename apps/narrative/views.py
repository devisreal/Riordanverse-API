from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from apps.core.filters import SortOrderingFilter
from apps.images.filters import ImageFilter
from apps.images.models import Image
from apps.images.serializers import ImageSerializer
from apps.narrative.filters import BookFilter, EventFilter, ProphecyFilter, QuestFilter
from apps.narrative.models import Book, BookImage, Event, Prophecy, Quest
from apps.narrative.serializers import (
    BookDetailSerializer,
    BookListSerializer,
    EventDetailSerializer,
    EventListSerializer,
    ProphecyDetailSerializer,
    ProphecyListSerializer,
    QuestDetailSerializer,
    QuestListSerializer,
)


class BookListView(generics.ListAPIView):
    """GET /api/v1/books/"""

    queryset = (
        Book.objects.prefetch_related('images__image', 'main_characters', 'antagonists')
        .select_related('narrator')
        .all()
    )
    serializer_class = BookListSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = BookFilter
    ordering_fields = ('book_number', 'published_date', 'title')
    ordering = ('series', 'book_number')


class BookDetailView(generics.RetrieveAPIView):
    """GET /api/v1/books/<slug>/"""

    queryset = (
        Book.objects.prefetch_related(
            'images__image',
            'main_characters',
            'antagonists',
            'narrator_records__character',
            'narrator_records__god',
            'narrator_records__titan',
            'narrator_records__monster',
            'narrator_records__creature',
            'main_character_records__character',
            'main_character_records__god',
            'main_character_records__titan',
            'main_character_records__monster',
            'main_character_records__creature',
            'antagonist_records__character',
            'antagonist_records__god',
            'antagonist_records__titan',
            'antagonist_records__monster',
            'antagonist_records__creature',
            'included_stories',
        )
        .select_related('narrator', 'parent_collection')
        .all()
    )
    serializer_class = BookDetailSerializer
    lookup_field = 'slug'


class BookImageListView(generics.ListAPIView):
    """GET /api/v1/books/<slug>/images/"""

    serializer_class = ImageSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = ImageFilter

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Image.objects.none()
        get_object_or_404(Book, slug=self.kwargs['slug'])
        book_images = BookImage.objects.filter(book__slug=self.kwargs['slug'])
        gallery_order = Subquery(
            book_images.filter(image_id=OuterRef('pk')).values('display_order')[:1]
        )
        return (
            Image.objects.filter(pk__in=book_images.values('image_id'))
            .annotate(_gallery_order=gallery_order)
            .order_by('_gallery_order', 'pk')
        )


# ---------------------------------------------------------------------------
# Prophecy views
# ---------------------------------------------------------------------------


class ProphecyListView(generics.ListAPIView):
    """GET /api/v1/prophecies/"""

    queryset = Prophecy.objects.prefetch_related(
        'subject',
        'books_relevant_to',
    ).select_related('delivered_by', 'fulfilled_in')
    serializer_class = ProphecyListSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = ProphecyFilter
    ordering_fields = ('title',)
    ordering = ('title',)


class ProphecyDetailView(generics.RetrieveAPIView):
    """GET /api/v1/prophecies/:slug/"""

    queryset = Prophecy.objects.prefetch_related(
        'subject',
        'subject_records__subject_character',
        'subject_records__subject_god',
        'subject_records__subject_titan',
        'subject_records__subject_monster',
        'books_relevant_to',
    ).select_related('delivered_by', 'fulfilled_in')
    serializer_class = ProphecyDetailSerializer
    lookup_field = 'slug'


# ---------------------------------------------------------------------------
# Quest views
# ---------------------------------------------------------------------------


class QuestListView(generics.ListAPIView):
    """GET /api/v1/quests/"""

    queryset = Quest.objects.prefetch_related(
        'participants',
        'casualties',
        'locations_visited',
        'monsters_encountered',
        'items_recovered',
    ).select_related('book', 'led_by', 'prophecy')
    serializer_class = QuestListSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = QuestFilter
    ordering_fields = ('title', 'book__book_number')
    ordering = ('book__book_number',)


class QuestDetailView(generics.RetrieveAPIView):
    """GET /api/v1/quests/:slug/"""

    queryset = Quest.objects.prefetch_related(
        'participant_records__participant_character',
        'participant_records__participant_god',
        'participant_records__participant_titan',
        'participant_records__participant_monster',
        'casualty_records__casualty_character',
        'casualty_records__casualty_god',
        'casualty_records__casualty_titan',
        'casualty_records__casualty_monster',
        'participants',
        'casualties',
        'locations_visited',
        'monsters_encountered',
        'items_recovered',
    ).select_related('book', 'led_by', 'prophecy')
    serializer_class = QuestDetailSerializer
    lookup_field = 'slug'


class QuestParticipantListView(generics.ListAPIView):
    """GET /api/v1/quests/:slug/participants/"""

    def get_queryset(self):
        from apps.characters.models import Character

        if getattr(self, 'swagger_fake_view', False):
            return Character.objects.none()
        get_object_or_404(Quest, slug=self.kwargs['slug'])
        return Character.objects.filter(quests_participated_in__slug=self.kwargs['slug']).distinct()

    def get_serializer_class(self):
        from apps.characters.serializers import CharacterListSerializer

        return CharacterListSerializer


# ---------------------------------------------------------------------------
# Event views
# ---------------------------------------------------------------------------


class EventListView(generics.ListAPIView):
    """GET /api/v1/events/"""

    queryset = Event.objects.prefetch_related(
        'participant_characters',
        'participant_gods',
        'participant_titans',
        'participant_monsters',
        'casualties',
    ).select_related('book', 'location')
    serializer_class = EventListSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = EventFilter
    ordering_fields = ('name', 'book__book_number')
    ordering = ('book__book_number', 'name')


class EventDetailView(generics.RetrieveAPIView):
    """GET /api/v1/events/:slug/"""

    queryset = Event.objects.prefetch_related(
        'casualty_records__casualty_character',
        'casualty_records__casualty_god',
        'casualty_records__casualty_titan',
        'casualty_records__casualty_monster',
        'participant_characters',
        'participant_gods',
        'participant_titans',
        'participant_monsters',
        'casualties',
    ).select_related('book', 'location')
    serializer_class = EventDetailSerializer
    lookup_field = 'slug'


# ---------------------------------------------------------------------------
# Book sub-resource views (deferred from feature/book-model)
# ---------------------------------------------------------------------------


class BookCharacterListView(generics.ListAPIView):
    """GET /api/v1/books/:slug/characters/"""

    def get_queryset(self):
        from apps.characters.models import Character

        if getattr(self, 'swagger_fake_view', False):
            return Character.objects.none()
        get_object_or_404(Book, slug=self.kwargs['slug'])
        return Character.objects.filter(books_appeared_in__slug=self.kwargs['slug']).distinct()

    def get_serializer_class(self):
        from apps.characters.serializers import CharacterListSerializer

        return CharacterListSerializer


class BookGodListView(generics.ListAPIView):
    """GET /api/v1/books/:slug/gods/"""

    def get_queryset(self):
        from apps.divinities.models import God

        if getattr(self, 'swagger_fake_view', False):
            return God.objects.none()
        get_object_or_404(Book, slug=self.kwargs['slug'])
        return God.objects.filter(books_appeared_in__slug=self.kwargs['slug']).distinct()

    def get_serializer_class(self):
        from apps.divinities.serializers import GodListSerializer

        return GodListSerializer


class BookMonsterListView(generics.ListAPIView):
    """GET /api/v1/books/:slug/monsters/"""

    def get_queryset(self):
        from apps.bestiary.models import Monster

        if getattr(self, 'swagger_fake_view', False):
            return Monster.objects.none()
        get_object_or_404(Book, slug=self.kwargs['slug'])
        return Monster.objects.filter(books_appeared_in__slug=self.kwargs['slug']).distinct()

    def get_serializer_class(self):
        from apps.bestiary.serializers import MonsterListSerializer

        return MonsterListSerializer


class BookLocationListView(generics.ListAPIView):
    """GET /api/v1/books/:slug/locations/"""

    def get_queryset(self):
        from apps.locations.models import Location

        if getattr(self, 'swagger_fake_view', False):
            return Location.objects.none()
        get_object_or_404(Book, slug=self.kwargs['slug'])
        return Location.objects.filter(books_appeared_in__slug=self.kwargs['slug']).distinct()

    def get_serializer_class(self):
        from apps.locations.serializers import LocationListSerializer

        return LocationListSerializer


class BookQuestListView(generics.ListAPIView):
    """GET /api/v1/books/:slug/quests/"""

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Quest.objects.none()
        get_object_or_404(Book, slug=self.kwargs['slug'])
        return Quest.objects.filter(book__slug=self.kwargs['slug'])

    serializer_class = QuestListSerializer
