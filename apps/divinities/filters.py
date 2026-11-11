# ruff: noqa: RUF012


from apps.core.choices import (
    GOD_AFFILIATION_CHOICES,
    GOD_TIER_CHOICES,
    STATUS_CHOICES,
    TITAN_ALIGNMENT_CHOICES,
    TITAN_GENERATION_CHOICES,
)
from apps.core.filters import (
    LoreMetadataFilterSet,
    StrictBooleanFilter,
    StrictChoiceFilter,
)
from apps.divinities.models import God, Titan


class GodFilter(LoreMetadataFilterSet):
    tier = StrictChoiceFilter(choices=GOD_TIER_CHOICES)
    affiliation = StrictChoiceFilter(choices=GOD_AFFILIATION_CHOICES)
    status = StrictChoiceFilter(choices=STATUS_CHOICES)
    has_cabin = StrictBooleanFilter()
    is_big_three = StrictBooleanFilter()
    roman_only = StrictBooleanFilter()

    class Meta:
        model = God
        fields = ['tier', 'affiliation', 'status', 'has_cabin', 'is_big_three', 'roman_only']


class TitanFilter(LoreMetadataFilterSet):
    alignment = StrictChoiceFilter(choices=TITAN_ALIGNMENT_CHOICES)
    generation = StrictChoiceFilter(choices=TITAN_GENERATION_CHOICES)
    status = StrictChoiceFilter(choices=STATUS_CHOICES)

    class Meta:
        model = Titan
        fields = ['alignment', 'generation', 'status']
