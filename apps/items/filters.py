# ruff: noqa: RUF012

import django_filters

from apps.core.choices import MATERIAL_CHOICES, WEAPON_TYPE_CHOICES
from apps.core.filters import StrictChoiceFilter
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
    forged_by = django_filters.CharFilter(
        field_name='forged_by__slug',
        help_text='Filter by forger slug e.g. ?forged_by=hephaestus',
    )

    # Boolean filters
    transforms = django_filters.BooleanFilter()
    passes_through_mortals = django_filters.BooleanFilter()

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
            'forged_by',
            'transforms',
            'passes_through_mortals',
            'book',
        ]
