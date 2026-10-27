# ruff: noqa: RUF012

import django_filters
from django.db.models import Q

from apps.characters.models import Character
from apps.core.choices import (
    CHARACTER_TYPE_CHOICES,
    GENDER_CHOICES,
    GREEK_OR_ROMAN_CHOICES,
    SPECIES_CHOICES,
    STATUS_CHOICES,
)
from apps.core.filters import StrictChoiceFilter


class CharacterFilter(django_filters.FilterSet):
    character_type = StrictChoiceFilter(
        choices=CHARACTER_TYPE_CHOICES,
        field_name='character_type',
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
    is_demigod = django_filters.BooleanFilter()
    is_big_three_child = django_filters.BooleanFilter()
    is_hunter_of_artemis = django_filters.BooleanFilter()
    is_oracle = django_filters.BooleanFilter()
    is_possessed = django_filters.BooleanFilter()
    can_see_through_mist = django_filters.BooleanFilter()
    has_adhd = django_filters.BooleanFilter()

    # Cabin
    cabin = django_filters.NumberFilter(field_name='cabin_number')

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
