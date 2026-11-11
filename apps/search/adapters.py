# ruff: noqa: RUF012

import watson.search as watson
from watson.search import SearchAdapter

from apps.bestiary.models import Creature, Monster
from apps.characters.models import Character
from apps.divinities.models import God, Titan
from apps.items.models import Weapon
from apps.locations.models import Location
from apps.narrative.models import Book, Event, Prophecy, Quest
from apps.organizations.models import Cabin, Faction


class BaseLoreSearchAdapter(SearchAdapter):
    """Expose active lore records and their descriptions in Watson search."""

    def get_live_queryset(self):
        return self.model.objects.all()

    def get_description(self, obj):
        return getattr(obj, 'description', '') or ''


class AdditionalFieldsSearchAdapter(BaseLoreSearchAdapter):
    """Append adapter-specific text to the model fields indexed by Watson."""

    def get_additional_fields(self, obj):
        return ''

    def get_content(self, obj):
        content = super().get_content(obj)
        additional_fields = self.get_additional_fields(obj)
        return ' '.join(part for part in (content, additional_fields) if part)


class CharacterSearchAdapter(AdditionalFieldsSearchAdapter):
    fields = ['name', 'description', 'lore_notes', 'quote']

    def get_additional_fields(self, obj):
        parts = [*obj.aliases]
        if obj.fatal_flaw:
            parts.append(obj.fatal_flaw)
        return ' '.join(str(part) for part in parts)


class GodSearchAdapter(AdditionalFieldsSearchAdapter):
    fields = ['name', 'roman_name', 'description']

    def get_additional_fields(self, obj):
        parts = [str(domain) for domain in obj.domains]
        if obj.roman_name:
            parts.append(obj.roman_name)
        return ' '.join(parts)


class TitanSearchAdapter(AdditionalFieldsSearchAdapter):
    fields = ['name', 'role_in_series', 'description']

    def get_additional_fields(self, obj):
        return ' '.join(str(domain) for domain in obj.domains)


class MonsterSearchAdapter(AdditionalFieldsSearchAdapter):
    fields = ['name', 'physical_description', 'description', 'disguise_form']

    def get_additional_fields(self, obj):
        parts = [*obj.aliases]
        if obj.parent_entity:
            parts.append(obj.parent_entity)
        if obj.spoils_of_war:
            parts.append(obj.spoils_of_war)
        return ' '.join(str(part) for part in parts)


class CreatureSearchAdapter(BaseLoreSearchAdapter):
    fields = ['name', 'description', 'origin']


class WeaponSearchAdapter(AdditionalFieldsSearchAdapter):
    fields = ['name', 'true_name', 'description', 'origin_story']

    def get_additional_fields(self, obj):
        parts = [str(ability) for ability in obj.abilities]
        if obj.transform_trigger:
            parts.append(obj.transform_trigger)
        return ' '.join(parts)


class LocationSearchAdapter(AdditionalFieldsSearchAdapter):
    fields = [
        'name',
        'real_world_location',
        'description',
        'mythological_significance',
    ]

    def get_additional_fields(self, obj):
        return ' '.join(str(event) for event in obj.notable_events)


class BookSearchAdapter(BaseLoreSearchAdapter):
    fields = ['title', 'synopsis', 'short_description', 'camp_bead_description']

    def get_description(self, obj):
        return obj.short_description or obj.synopsis or ''


class QuestSearchAdapter(BaseLoreSearchAdapter):
    fields = ['title', 'objective', 'outcome', 'description', 'initiated_by']


class ProphecySearchAdapter(BaseLoreSearchAdapter):
    fields = ['title', 'text', 'interpretation_notes', 'oracle_type']


class EventSearchAdapter(BaseLoreSearchAdapter):
    fields = ['name', 'significance', 'description', 'outcome']


class CabinSearchAdapter(BaseLoreSearchAdapter):
    fields = ['architecture_description']

    def get_title(self, obj):
        deity_name = obj.deity.name if obj.deity else 'Honorary'
        return f'Cabin {obj.number} — {deity_name}'

    def get_description(self, obj):
        return obj.architecture_description or ''

    def get_live_queryset(self):
        # Watson uses this queryset when indexing all registered cabins.
        return Cabin.objects.select_related('deity')


class FactionSearchAdapter(BaseLoreSearchAdapter):
    fields = ['name', 'description']


ADAPTERS = (
    (Character, CharacterSearchAdapter),
    (God, GodSearchAdapter),
    (Titan, TitanSearchAdapter),
    (Monster, MonsterSearchAdapter),
    (Creature, CreatureSearchAdapter),
    (Weapon, WeaponSearchAdapter),
    (Location, LocationSearchAdapter),
    (Book, BookSearchAdapter),
    (Quest, QuestSearchAdapter),
    (Prophecy, ProphecySearchAdapter),
    (Event, EventSearchAdapter),
    (Cabin, CabinSearchAdapter),
    (Faction, FactionSearchAdapter),
)


def register_all():
    """Register each searchable lore model, safely allowing repeated calls."""
    for model, adapter_class in ADAPTERS:
        if not watson.is_registered(model):
            watson.register(model, adapter_class)
