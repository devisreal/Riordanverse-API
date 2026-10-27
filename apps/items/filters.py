# ruff: noqa: RUF012

import django_filters
from django.db.models import Q

from apps.core.choices import MATERIAL_CHOICES, WEAPON_TYPE_CHOICES
from apps.core.filters import StrictBooleanFilter, StrictChoiceFilter
from apps.items.models import Weapon


class WeaponFilter(django_filters.FilterSet):
    weapon_type = StrictChoiceFilter(choices=WEAPON_TYPE_CHOICES)
    material = StrictChoiceFilter(choices=MATERIAL_CHOICES)

    # Owner filters — only owner_primary is filterable
    # owner_history is JSONField narrative data, not filterable
    owner_character = django_filters.CharFilter(
        field_name='owner_primary_character__slug',
        help_text='Filter by character owner slug e.g. ?owner_character=percy-jackson',
    )
    owner_god = django_filters.CharFilter(
        field_name='owner_primary_god__slug',
        help_text='Filter by god owner slug e.g. ?owner_god=poseidon',
    )
    owner_titan = django_filters.CharFilter(
        field_name='owner_primary_titan__slug',
        help_text='Filter by Titan owner slug e.g. ?owner_titan=kronos',
    )
    forged_by = django_filters.CharFilter(
        method='filter_forged_by',
        help_text='Filter by God or character forger slug e.g. ?forged_by=hephaestus',
    )

    def filter_forged_by(self, queryset, name, value):
        return queryset.filter(
            Q(forged_by__slug=value) | Q(forged_by_character__slug=value)
        ).distinct()

    # Boolean filters
    transforms = StrictBooleanFilter()
    passes_through_mortals = StrictBooleanFilter()

    # Book filters
    book = django_filters.CharFilter(
        field_name='books_appeared_in__slug',
        help_text='Filter by book slug e.g. ?book=the-lightning-thief',
    )

    class Meta:
        model = Weapon
        fields = [
            'weapon_type',
            'material',
            'owner_character',
            'owner_god',
            'owner_titan',
            'forged_by',
            'transforms',
            'passes_through_mortals',
            'book',
        ]
