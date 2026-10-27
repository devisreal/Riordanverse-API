# ruff: noqa: RUF012

import django_filters

from apps.core.choices import FACTION_TYPE_CHOICES
from apps.core.filters import StrictBooleanFilter, StrictChoiceFilter
from apps.organizations.models import (
    CABIN_POSITION_CHOICES,
    FACTION_ALIGNMENT_CHOICES,
    Cabin,
    Faction,
)


class CabinFilter(django_filters.FilterSet):
    is_honorary = StrictBooleanFilter()
    is_empty = StrictBooleanFilter()
    position = StrictChoiceFilter(choices=CABIN_POSITION_CHOICES)
    deity = django_filters.CharFilter(
        field_name='deity__slug',
        help_text='Filter by deity slug e.g. ?deity=poseidon',
    )

    class Meta:
        model = Cabin
        fields = ['is_honorary', 'is_empty', 'position', 'deity']


class FactionFilter(django_filters.FilterSet):
    faction_type = StrictChoiceFilter(choices=FACTION_TYPE_CHOICES)
    alignment = StrictChoiceFilter(choices=FACTION_ALIGNMENT_CHOICES)
    book = django_filters.CharFilter(
        field_name='books_active_in__slug',
        help_text='Filter by book slug e.g. ?book=the-last-olympian',
    )

    class Meta:
        model = Faction
        fields = ['faction_type', 'alignment', 'book']
