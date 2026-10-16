import django_filters

from apps.core.choices import BOOK_TYPE_CHOICES, SERIES_CHOICES
from apps.core.filters import StrictChoiceFilter
from apps.narrative.models import Book


class BookFilter(django_filters.FilterSet):
    series = StrictChoiceFilter(choices=SERIES_CHOICES)
    book_type = StrictChoiceFilter(choices=BOOK_TYPE_CHOICES)

    class Meta:
        model = Book
        fields = ('series', 'book_type')
