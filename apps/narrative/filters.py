import django_filters

from apps.core.choices import BOOK_TYPE_CHOICES, EVENT_TYPE_CHOICES, SERIES_CHOICES
from apps.core.filters import LoreMetadataFilterSet, StrictChoiceFilter
from apps.narrative.models import Book, Event, Prophecy, Quest


class BookFilter(LoreMetadataFilterSet):
    series = StrictChoiceFilter(choices=SERIES_CHOICES)
    book_type = StrictChoiceFilter(choices=BOOK_TYPE_CHOICES)
    type = StrictChoiceFilter(choices=BOOK_TYPE_CHOICES, field_name='book_type')
    parent_collection = django_filters.CharFilter(
        field_name='parent_collection__slug',
        help_text='Filter by parent collection slug e.g. ?parent-collection=the-demigod-files',
    )
    narrator = django_filters.CharFilter(
        field_name='narrator_records__character__slug', distinct=True
    )
    narrator_character = django_filters.CharFilter(
        field_name='narrator_records__character__slug', distinct=True
    )
    narrator_god = django_filters.CharFilter(
        field_name='narrator_records__god__slug', distinct=True
    )
    narrator_titan = django_filters.CharFilter(
        field_name='narrator_records__titan__slug', distinct=True
    )
    narrator_monster = django_filters.CharFilter(
        field_name='narrator_records__monster__slug', distinct=True
    )
    narrator_creature = django_filters.CharFilter(
        field_name='narrator_records__creature__slug', distinct=True
    )
    main_character = django_filters.CharFilter(
        field_name='main_characters__slug',
        distinct=True,
        help_text='Filter by Character main-character slug.',
    )
    main_character_god = django_filters.CharFilter(
        field_name='main_character_records__god__slug', distinct=True
    )
    main_character_titan = django_filters.CharFilter(
        field_name='main_character_records__titan__slug', distinct=True
    )
    main_character_monster = django_filters.CharFilter(
        field_name='main_character_records__monster__slug', distinct=True
    )
    main_character_creature = django_filters.CharFilter(
        field_name='main_character_records__creature__slug', distinct=True
    )
    antagonist = django_filters.CharFilter(
        field_name='antagonists__slug',
        distinct=True,
        help_text='Filter by Character antagonist slug.',
    )
    antagonist_god = django_filters.CharFilter(
        field_name='antagonist_records__god__slug', distinct=True
    )
    antagonist_titan = django_filters.CharFilter(
        field_name='antagonist_records__titan__slug', distinct=True
    )
    antagonist_monster = django_filters.CharFilter(
        field_name='antagonist_records__monster__slug', distinct=True
    )
    antagonist_creature = django_filters.CharFilter(
        field_name='antagonist_records__creature__slug', distinct=True
    )

    class Meta:
        model = Book
        fields = (
            'series',
            'book_type',
            'type',
            'parent_collection',
            'narrator',
            'narrator_character',
            'narrator_god',
            'narrator_titan',
            'narrator_monster',
            'narrator_creature',
            'main_character',
            'main_character_god',
            'main_character_titan',
            'main_character_monster',
            'main_character_creature',
            'antagonist',
            'antagonist_god',
            'antagonist_titan',
            'antagonist_monster',
            'antagonist_creature',
        )

    def __init__(self, data=None, *args, **kwargs):
        if data is not None and 'parent-collection' in data:
            data = data.copy()
            data['parent_collection'] = data['parent-collection']
        super().__init__(data, *args, **kwargs)


class ProphecyFilter(LoreMetadataFilterSet):
    fulfilled_in = django_filters.CharFilter(
        field_name='fulfilled_in__slug',
        help_text='Filter by book slug e.g. ?fulfilled_in=the-last-olympian',
    )
    subject = django_filters.CharFilter(
        field_name='subject__slug',
        help_text='Filter by Character subject slug e.g. ?subject=percy-jackson',
    )
    subject_god = django_filters.CharFilter(
        field_name='subject_records__subject_god__slug',
        help_text='Filter by God subject slug e.g. ?subject_god=ares',
    )
    subject_titan = django_filters.CharFilter(
        field_name='subject_records__subject_titan__slug',
        help_text='Filter by Titan subject slug e.g. ?subject_titan=atlas',
    )
    subject_monster = django_filters.CharFilter(
        field_name='subject_records__subject_monster__slug',
        help_text='Filter by Monster subject slug.',
    )
    book = django_filters.CharFilter(
        field_name='books_relevant_to__slug',
    )

    class Meta:
        model = Prophecy
        fields = (
            'fulfilled_in',
            'subject',
            'subject_god',
            'subject_titan',
            'subject_monster',
            'book',
        )


class QuestFilter(LoreMetadataFilterSet):
    book = django_filters.CharFilter(
        field_name='book__slug',
        help_text='Filter by book slug e.g. ?book=the-sea-of-monsters',
    )
    led_by = django_filters.CharFilter(
        field_name='led_by__slug',
        help_text='Filter by character slug e.g. ?led_by=percy-jackson',
    )
    participant = django_filters.CharFilter(
        field_name='participants__slug',
        help_text='Filter by Character participant slug e.g. ?participant=annabeth-chase',
    )
    participant_god = django_filters.CharFilter(
        field_name='participant_records__participant_god__slug',
    )
    participant_titan = django_filters.CharFilter(
        field_name='participant_records__participant_titan__slug',
    )
    participant_monster = django_filters.CharFilter(
        field_name='participant_records__participant_monster__slug',
    )
    casualty = django_filters.CharFilter(field_name='casualties__slug')
    casualty_god = django_filters.CharFilter(
        field_name='casualty_records__casualty_god__slug',
    )
    casualty_titan = django_filters.CharFilter(
        field_name='casualty_records__casualty_titan__slug',
    )
    casualty_monster = django_filters.CharFilter(
        field_name='casualty_records__casualty_monster__slug',
    )

    class Meta:
        model = Quest
        fields = (
            'book',
            'led_by',
            'participant',
            'participant_god',
            'participant_titan',
            'participant_monster',
            'casualty',
            'casualty_god',
            'casualty_titan',
            'casualty_monster',
        )


class EventFilter(LoreMetadataFilterSet):
    event_type = StrictChoiceFilter(choices=EVENT_TYPE_CHOICES)
    type = StrictChoiceFilter(choices=EVENT_TYPE_CHOICES, field_name='event_type')
    book = django_filters.CharFilter(field_name='book__slug')
    location = django_filters.CharFilter(field_name='location__slug')
    participant_character = django_filters.CharFilter(
        field_name='participant_characters__slug',
    )
    participant_god = django_filters.CharFilter(
        field_name='participant_gods__slug',
    )
    participant_titan = django_filters.CharFilter(
        field_name='participant_titans__slug',
    )
    participant_monster = django_filters.CharFilter(
        field_name='participant_monsters__slug',
    )
    casualty = django_filters.CharFilter(field_name='casualties__slug')
    casualty_god = django_filters.CharFilter(
        field_name='casualty_records__casualty_god__slug',
    )
    casualty_titan = django_filters.CharFilter(
        field_name='casualty_records__casualty_titan__slug',
    )
    casualty_monster = django_filters.CharFilter(
        field_name='casualty_records__casualty_monster__slug',
    )

    class Meta:
        model = Event
        fields = (
            'event_type',
            'type',
            'book',
            'location',
            'participant_character',
            'participant_god',
            'participant_titan',
            'participant_monster',
            'casualty',
            'casualty_god',
            'casualty_titan',
            'casualty_monster',
        )
