# ruff: noqa: RUF012

import django_filters
from django.db import connection
from django.db.models import CharField, Q
from django.db.models.functions import Cast

from apps.characters.models import (
    POWER_SOURCE_CHOICES,
    POWER_TYPE_CHOICES,
    Character,
    Power,
)
from apps.core.choices import (
    AFFILIATION_CHOICES,
    CHARACTER_TYPE_CHOICES,
    GENDER_CHOICES,
    GREEK_OR_ROMAN_CHOICES,
    SPECIES_CHOICES,
    STATUS_CHOICES,
)
from apps.core.filters import (
    LoreMetadataFilterSet,
    StrictBooleanFilter,
    StrictChoiceFilter,
)


class PowerFilter(django_filters.FilterSet):
    """Filters available on a Character's nested Power collection."""

    source = StrictChoiceFilter(choices=POWER_SOURCE_CHOICES)
    type = StrictChoiceFilter(choices=POWER_TYPE_CHOICES)
    is_passive = StrictBooleanFilter()

    class Meta:
        model = Power
        fields = ('source', 'type', 'is_passive')


class CharacterFilter(LoreMetadataFilterSet):
    character_type = StrictChoiceFilter(
        choices=CHARACTER_TYPE_CHOICES,
        field_name='character_type',
    )
    type = StrictChoiceFilter(choices=CHARACTER_TYPE_CHOICES, field_name='character_type')
    affiliation = StrictChoiceFilter(
        choices=AFFILIATION_CHOICES,
        method='filter_affiliation',
    )
    species = StrictChoiceFilter(choices=SPECIES_CHOICES)
    status = StrictChoiceFilter(choices=STATUS_CHOICES)
    gender = StrictChoiceFilter(choices=GENDER_CHOICES)
    greek_or_roman = StrictChoiceFilter(choices=GREEK_OR_ROMAN_CHOICES)

    # FK filters
    divine_parent = django_filters.CharFilter(
        method='filter_divine_parent',
        help_text='Filter by divine parent slug e.g. ?divine_parent=poseidon',
    )
    first_appearance_book = django_filters.CharFilter(
        field_name='first_appearance_book__slug',
    )
    book = django_filters.CharFilter(
        field_name='books_appeared_in__slug',
        help_text='Filter by book slug e.g. ?book=the-lightning-thief',
    )

    # Boolean filters
    is_demigod = StrictBooleanFilter()
    is_big_three_child = StrictBooleanFilter()
    is_hunter_of_artemis = StrictBooleanFilter()
    is_oracle = StrictBooleanFilter()
    is_possessed = StrictBooleanFilter()
    can_see_through_mist = StrictBooleanFilter()
    has_adhd = StrictBooleanFilter()

    # Cabin
    cabin = django_filters.NumberFilter(field_name='cabin_number')

    def filter_affiliation(self, queryset, name, value):
        if connection.features.supports_json_field_contains:
            return queryset.filter(affiliation__contains=[value]).distinct()
        return (
            queryset.annotate(_affiliation_text=Cast('affiliation', output_field=CharField()))
            .filter(_affiliation_text__contains=f'"{value}"')
            .distinct()
        )

    def filter_divine_parent(self, queryset, name, value):
        return queryset.filter(
            Q(
                divine_relationships_as_to__relationship_type='parent_of',
                divine_relationships_as_to__from_god__slug=value,
            )
            | Q(
                divine_relationships_as_to__relationship_type='parent_of',
                divine_relationships_as_to__from_titan__slug=value,
            )
        ).distinct()

    class Meta:
        model = Character
        fields = [
            'character_type',
            'type',
            'affiliation',
            'species',
            'status',
            'gender',
            'greek_or_roman',
            'divine_parent',
            'first_appearance_book',
            'book',
            'is_demigod',
            'is_big_three_child',
            'is_hunter_of_artemis',
            'is_oracle',
            'is_possessed',
            'can_see_through_mist',
            'has_adhd',
            'cabin',
        ]
