"""Small shared model factories used by the project's tests.

Factories create saved objects with reasonable defaults. Pass keyword arguments
when a test needs a particular field value.
"""


def make_book(**kwargs):
    from apps.narrative.models import Book

    defaults = {
        'title': 'Test Book',
        'series': 'percy_jackson_and_the_olympians',
        'book_number': 1,
        'book_type': 'novel',
    }
    defaults.update(kwargs)
    return Book.objects.create(**defaults)


def make_god(**kwargs):
    from apps.divinities.models import God

    defaults = {
        'name': 'Test God',
        'tier': 'olympian',
        'affiliation': 'olympian_council',
        'status': 'immortal',
    }
    defaults.update(kwargs)
    return God.objects.create(**defaults)


def make_titan(**kwargs):
    from apps.divinities.models import Titan

    defaults = {
        'name': 'Test Titan',
        'generation': 'elder_titan',
        'status': 'imprisoned',
        'alignment': 'kronos_army',
    }
    defaults.update(kwargs)
    return Titan.objects.create(**defaults)


def make_divine_relationship(from_entity, to_entity, relationship_type='parent_of', **kwargs):
    """Create a relationship between God/Titan entities."""
    from apps.divinities.models import DivineRelationship, God, Titan

    data = {'relationship_type': relationship_type}
    if isinstance(from_entity, God):
        data['from_god'] = from_entity
    elif isinstance(from_entity, Titan):
        data['from_titan'] = from_entity
    else:
        raise TypeError('from_entity must be a God or Titan instance')

    if isinstance(to_entity, God):
        data['to_god'] = to_entity
    elif isinstance(to_entity, Titan):
        data['to_titan'] = to_entity
    else:
        raise TypeError('to_entity must be a God or Titan instance')

    data.update(kwargs)
    return DivineRelationship.objects.create(**data)


def make_character(**kwargs):
    from apps.characters.models import Character

    defaults = {
        'name': 'Test Character',
        'character_type': 'demigod',
        'species': 'demigod',
        'status': 'alive',
    }
    defaults.update(kwargs)
    return Character.objects.create(**defaults)


def make_power(character, **kwargs):
    from apps.characters.models import Power

    defaults = {'character': character, 'name': 'Test Power'}
    defaults.update(kwargs)
    return Power.objects.create(**defaults)


def make_weapon(**kwargs):
    from apps.items.models import Weapon

    defaults = {'name': 'Test Weapon', 'weapon_type': 'sword'}
    defaults.update(kwargs)
    return Weapon.objects.create(**defaults)


def make_monster(**kwargs):
    from apps.bestiary.models import Monster

    defaults = {'name': 'Test Monster', 'monster_type': 'chimeric', 'allegiance': 'independent'}
    defaults.update(kwargs)
    return Monster.objects.create(**defaults)


def make_creature(**kwargs):
    from apps.bestiary.models import Creature

    defaults = {'name': 'Test Creature', 'alignment': 'neutral'}
    defaults.update(kwargs)
    return Creature.objects.create(**defaults)


def make_location(**kwargs):
    from apps.locations.models import Location

    defaults = {'name': 'Test Location', 'location_type': 'mortal_city'}
    defaults.update(kwargs)
    return Location.objects.create(**defaults)


def make_cabin(**kwargs):
    from apps.organizations.models import Cabin

    defaults = {'number': 99}
    defaults.update(kwargs)
    return Cabin.objects.create(**defaults)


def make_faction(**kwargs):
    from apps.organizations.models import Faction

    defaults = {'name': 'Test Faction', 'faction_type': 'group', 'alignment': 'olympian'}
    defaults.update(kwargs)
    return Faction.objects.create(**defaults)
