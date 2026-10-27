# ruff: noqa: RUF012

from django.db import migrations

ENTITY_TYPES = ('god', 'titan', 'character', 'monster', 'creature')


def _edge_kwargs(from_type, from_entity, to_type, to_entity, relationship_type):
    return {
        **{
            f'from_{entity_type}_id': from_entity.pk if entity_type == from_type else None
            for entity_type in ENTITY_TYPES
        },
        **{
            f'to_{entity_type}_id': to_entity.pk if entity_type == to_type else None
            for entity_type in ENTITY_TYPES
        },
        'relationship_type': relationship_type,
    }


def _entity_for_side(relationship, side):
    for entity_type in ENTITY_TYPES:
        entity = getattr(relationship, f'{side}_{entity_type}', None)
        if entity is not None:
            return entity_type, entity
    return None, None


def _ensure_edge(Relationship, from_type, from_entity, to_type, to_entity, relationship_type):
    if from_entity is None or to_entity is None:
        return
    if from_type == to_type and from_entity.pk == to_entity.pk:
        return
    Relationship.objects.get_or_create(
        **_edge_kwargs(from_type, from_entity, to_type, to_entity, relationship_type)
    )


def migrate_existing_family_links(apps, schema_editor):
    God = apps.get_model('divinities', 'God')
    Character = apps.get_model('characters', 'Character')
    Relationship = apps.get_model('divinities', 'DivineRelationship')

    # Normalize historical child_of tuples into the single canonical parent_of direction.
    endpoint_fields = [f'{side}_{kind}' for side in ('from', 'to') for kind in ENTITY_TYPES]
    for relationship in list(Relationship.objects.filter(relationship_type='child_of')):
        from_type, from_entity = _entity_for_side(relationship, 'from')
        to_type, to_entity = _entity_for_side(relationship, 'to')
        reverse = _edge_kwargs(to_type, to_entity, from_type, from_entity, 'parent_of')
        if Relationship.objects.filter(**reverse).exclude(pk=relationship.pk).exists():
            relationship.delete()
            continue
        for field in endpoint_fields:
            setattr(relationship, f'{field}_id', reverse.get(f'{field}_id'))
        relationship.relationship_type = 'parent_of'
        relationship.save(update_fields=(*endpoint_fields, 'relationship_type'))

    # Preserve existing rows and ensure symmetric relationships have reverse rows.
    for relationship in list(
        Relationship.objects.filter(relationship_type__in=('sibling_of', 'consort_of'))
    ):
        from_type, from_entity = _entity_for_side(relationship, 'from')
        to_type, to_entity = _entity_for_side(relationship, 'to')
        _ensure_edge(
            Relationship,
            to_type,
            to_entity,
            from_type,
            from_entity,
            relationship.relationship_type,
        )

    # Move legacy direct parent data into the unified graph without deleting the old fields.
    for character in Character.objects.select_related(
        'divine_parent', 'divine_parent_titan', 'mortal_parent_ref'
    ).iterator():
        if character.divine_parent_id:
            _ensure_edge(
                Relationship,
                'god',
                character.divine_parent,
                'character',
                character,
                'parent_of',
            )
        if character.divine_parent_titan_id:
            _ensure_edge(
                Relationship,
                'titan',
                character.divine_parent_titan,
                'character',
                character,
                'parent_of',
            )
        if character.mortal_parent_ref_id:
            _ensure_edge(
                Relationship,
                'character',
                character.mortal_parent_ref,
                'character',
                character,
                'parent_of',
            )
        for sibling in character.siblings.all():
            _ensure_edge(
                Relationship,
                'character',
                character,
                'character',
                sibling,
                'sibling_of',
            )

    # God.children_demigods is another historical projection of parentage.
    for god in God.objects.iterator():
        for child in god.children_demigods.all():
            _ensure_edge(Relationship, 'god', god, 'character', child, 'parent_of')


def reverse_family_migration(apps, schema_editor):
    Relationship = apps.get_model('divinities', 'DivineRelationship')
    Relationship.objects.filter(
        from_monster__isnull=False,
    ).delete()
    Relationship.objects.filter(
        to_monster__isnull=False,
    ).delete()
    Relationship.objects.filter(
        from_creature__isnull=False,
    ).delete()
    Relationship.objects.filter(
        to_creature__isnull=False,
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('divinities', '0009_expand_family_relationships'),
        ('characters', '0006_power_wiki_url'),
        ('bestiary', '0004_creaturemember_alter_creature_notable_members_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_existing_family_links, reverse_family_migration),
    ]
