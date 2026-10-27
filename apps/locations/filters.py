# ruff: noqa: RUF012

import django_filters

from apps.core.choices import LOCATION_TYPE_CHOICES
from apps.core.filters import StrictBooleanFilter, StrictChoiceFilter
from apps.locations.models import Location


class LocationFilter(django_filters.FilterSet):
    location_type = StrictChoiceFilter(choices=LOCATION_TYPE_CHOICES)
    is_hidden_from_mortals = StrictBooleanFilter()

    # controlled_by filters — one per entity type
    controlled_by_god = django_filters.CharFilter(
        field_name='controlled_by_god__slug',
        help_text='Filter by god slug e.g. ?controlled_by_god=hades',
    )
    controlled_by_titan = django_filters.CharFilter(
        field_name='controlled_by_titan__slug',
        help_text='Filter by titan slug e.g. ?controlled_by_titan=atlas',
    )
    controlled_by_character = django_filters.CharFilter(
        field_name='controlled_by_character__slug',
        help_text='Filter by character slug e.g. ?controlled_by_character=luke-castellan',
    )
    controlled_by_monster = django_filters.CharFilter(
        field_name='controlled_by_monster__slug',
        help_text='Filter by monster slug e.g. ?controlled_by_monster=polyphemus',
    )

    book = django_filters.CharFilter(
        field_name='books_appeared_in__slug',
        help_text='Filter by book slug e.g. ?book=the-titans-curse',
    )

    class Meta:
        model = Location
        fields = [
            'location_type',
            'is_hidden_from_mortals',
            'controlled_by_god',
            'controlled_by_titan',
            'controlled_by_character',
            'controlled_by_monster',
            'book',
        ]
