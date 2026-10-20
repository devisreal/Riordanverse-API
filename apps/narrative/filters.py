import django_filters

from apps.core.choices import BOOK_TYPE_CHOICES, EVENT_TYPE_CHOICES, SERIES_CHOICES
from apps.core.filters import StrictChoiceFilter
from apps.narrative.models import Book, Event, Prophecy, Quest


class BookFilter(django_filters.FilterSet):
    series = StrictChoiceFilter(choices=SERIES_CHOICES)
    book_type = StrictChoiceFilter(choices=BOOK_TYPE_CHOICES)
    parent_collection = django_filters.CharFilter(
        field_name='parent_collection__slug',
        help_text='Filter by parent collection slug e.g. ?parent-collection=the-demigod-files',
    )

    class Meta:
        model = Book
        fields = ('series', 'book_type', 'parent_collection')

    def __init__(self, data=None, *args, **kwargs):
        if data is not None and 'parent-collection' in data:
            data = data.copy()
            data['parent_collection'] = data['parent-collection']
        super().__init__(data, *args, **kwargs)


class ProphecyFilter(django_filters.FilterSet):
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


class QuestFilter(django_filters.FilterSet):
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
        help_text='Filter by participant slug e.g. ?participant=annabeth-chase',
    )

    class Meta:
        model = Quest
        fields = ('book', 'led_by', 'participant')


class EventFilter(django_filters.FilterSet):
    event_type = StrictChoiceFilter(choices=EVENT_TYPE_CHOICES)
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

    class Meta:
        model = Event
        fields = (
            'event_type',
            'book',
            'location',
            'participant_character',
            'participant_god',
            'participant_titan',
        )
