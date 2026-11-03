from django.db.models import Prefetch, Q

from apps.bestiary.models import Creature, Monster
from apps.characters.models import Character
from apps.divinities.models import DivineRelationship, God, Titan

ENTITY_TYPES = ('god', 'titan', 'character', 'monster', 'creature')
RELATIONSHIP_RELATED_NAMES = {
    'god': ('relationships_as_from', 'relationships_as_to'),
    'titan': ('relationships_as_from', 'relationships_as_to'),
    'character': ('divine_relationships_as_from', 'divine_relationships_as_to'),
    'monster': ('family_relationships_as_from', 'family_relationships_as_to'),
    'creature': ('family_relationships_as_from', 'family_relationships_as_to'),
}
ENTITY_MODELS = {
    'god': God,
    'titan': Titan,
    'character': Character,
    'monster': Monster,
    'creature': Creature,
}


def relationship_filters(entity):
    entity_type = next(
        (name for name, model in ENTITY_MODELS.items() if isinstance(entity, model)),
        None,
    )
    if entity_type is None:
        raise TypeError(f'Unsupported family entity: {type(entity).__name__}')
    return entity_type, Q(**{f'from_{entity_type}': entity}), Q(**{f'to_{entity_type}': entity})


def _related_entity(relationship, side):
    for entity_type in ENTITY_TYPES:
        entity = getattr(relationship, f'{side}_{entity_type}')
        if entity is not None and not getattr(entity, 'is_deleted', False):
            return {
                'name': entity.name,
                'type': entity_type,
                'slug': entity.slug,
            }
    return None


def prefetch_family(queryset):
    entity_type = next(
        (kind for kind, model in ENTITY_MODELS.items() if queryset.model is model),
        None,
    )
    if entity_type is None:
        raise TypeError(f'Unsupported family queryset: {queryset.model.__name__}')
    from_name, to_name = RELATIONSHIP_RELATED_NAMES[entity_type]
    related_queryset = DivineRelationship.objects.select_related(
        *(f'from_{kind}' for kind in ENTITY_TYPES),
        *(f'to_{kind}' for kind in ENTITY_TYPES),
    )
    return queryset.prefetch_related(
        Prefetch(from_name, queryset=related_queryset, to_attr='_family_from_relationships'),
        Prefetch(to_name, queryset=related_queryset, to_attr='_family_to_relationships'),
    )


def serialize_family(entity):
    entity_type, from_filter, to_filter = relationship_filters(entity)
    from_relationships = getattr(entity, '_family_from_relationships', None)
    to_relationships = getattr(entity, '_family_to_relationships', None)
    if from_relationships is not None and to_relationships is not None:
        relationships = (*from_relationships, *to_relationships)
    else:
        relationships = DivineRelationship.objects.filter(from_filter | to_filter).select_related(
            *(f'from_{kind}' for kind in ENTITY_TYPES),
            *(f'to_{kind}' for kind in ENTITY_TYPES),
        )
    family = {category: {} for category in ('parents', 'siblings', 'consorts', 'children')}

    for relationship in relationships:
        relationship_type = relationship.relationship_type
        if relationship_type in ('parent_of', 'child_of'):
            parent_side, child_side = (
                ('from', 'to') if relationship_type == 'parent_of' else ('to', 'from')
            )
            if getattr(relationship, f'{child_side}_{entity_type}_id') == entity.pk:
                related = _related_entity(relationship, parent_side)
                category = 'parents'
            elif getattr(relationship, f'{parent_side}_{entity_type}_id') == entity.pk:
                related = _related_entity(relationship, child_side)
                category = 'children'
            else:
                continue
        elif relationship_type in ('sibling_of', 'consort_of'):
            from_is_entity = getattr(relationship, f'from_{entity_type}_id') == entity.pk
            related = _related_entity(relationship, 'to' if from_is_entity else 'from')
            category = 'siblings' if relationship_type == 'sibling_of' else 'consorts'
        else:
            continue

        if related is not None:
            family[category][(related['type'], related['slug'])] = related

    return {
        category: sorted(
            relations.values(),
            key=lambda item: (item['name'].casefold(), item['type'], item['slug']),
        )
        for category, relations in family.items()
    }
