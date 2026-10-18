import django_filters

from apps.bestiary.models import (
    CREATURE_ALIGNMENT_CHOICES,
    Creature,
    Monster,
)
from apps.core.choices import MONSTER_ALLEGIANCE_CHOICES, MONSTER_TYPE_CHOICES
from apps.core.filters import StrictChoiceFilter


class MonsterFilter(django_filters.FilterSet):
    monster_type = StrictChoiceFilter(choices=MONSTER_TYPE_CHOICES)
    allegiance = StrictChoiceFilter(choices=MONSTER_ALLEGIANCE_CHOICES)
    can_reform = django_filters.BooleanFilter()
    defeated_by = django_filters.CharFilter(
        field_name='defeated_by__slug',
        help_text='Filter by character slug e.g. ?defeated_by=percy-jackson',
    )
    book = django_filters.CharFilter(
        field_name='books_appeared_in__slug',
        help_text='Filter by book slug e.g. ?book=the-lightning-thief',
    )

    class Meta:
        model = Monster
        fields = ('monster_type', 'allegiance', 'can_reform', 'defeated_by', 'book')


class CreatureFilter(django_filters.FilterSet):
    alignment = StrictChoiceFilter(choices=CREATURE_ALIGNMENT_CHOICES)

    class Meta:
        model = Creature
        fields = ('alignment',)
