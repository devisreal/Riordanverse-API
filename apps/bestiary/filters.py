import django_filters

from apps.bestiary.models import (
    CREATURE_ALIGNMENT_CHOICES,
    Creature,
    Monster,
)
from apps.core.choices import MONSTER_ALLEGIANCE_CHOICES, MONSTER_TYPE_CHOICES
from apps.core.filters import StrictBooleanFilter, StrictChoiceFilter


class MonsterFilter(django_filters.FilterSet):
    monster_type = StrictChoiceFilter(choices=MONSTER_TYPE_CHOICES)
    type = StrictChoiceFilter(choices=MONSTER_TYPE_CHOICES, field_name='monster_type')
    allegiance = StrictChoiceFilter(choices=MONSTER_ALLEGIANCE_CHOICES)
    can_reform = StrictBooleanFilter()
    defeated_by = django_filters.CharFilter(
        field_name='defeated_by__slug',
        help_text='Filter by character slug e.g. ?defeated_by=percy-jackson',
    )
    defeated_by_god = django_filters.CharFilter(
        field_name='defeated_by_gods__slug',
        help_text='Filter by God slug e.g. ?defeated_by_god=zeus',
    )
    defeated_in_book = django_filters.CharFilter(
        field_name='defeats__book__slug',
        distinct=True,
        help_text='Filter by the book in which a defeat occurred, e.g. ?defeated_in_book=the-sea-of-monsters',
    )
    book = django_filters.CharFilter(
        field_name='books_appeared_in__slug',
        help_text='Filter by book slug e.g. ?book=the-lightning-thief',
    )

    class Meta:
        model = Monster
        fields = (
            'monster_type',
            'type',
            'allegiance',
            'can_reform',
            'defeated_by',
            'defeated_by_god',
            'defeated_in_book',
            'book',
        )


class CreatureFilter(django_filters.FilterSet):
    alignment = StrictChoiceFilter(choices=CREATURE_ALIGNMENT_CHOICES)

    class Meta:
        model = Creature
        fields = ('alignment',)
