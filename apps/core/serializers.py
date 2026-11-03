from django.db import models
from rest_framework import serializers

from apps.core.models import BaseModel, LoreSource


def active_lore_entity(entity):
    if entity is not None and getattr(entity, 'is_deleted', False):
        return None
    return entity


def active_lore_slug(entity):
    entity = active_lore_entity(entity)
    return entity.slug if entity is not None else None


def active_lore_reference(entity, entity_type):
    entity = active_lore_entity(entity)
    if entity is None:
        return None
    return {'type': entity_type, 'slug': entity.slug, 'name': entity.name}


class ActiveRelatedModelSerializer(serializers.ModelSerializer):
    """Hide through-records that point to soft-deleted lore entities."""

    def to_representation(self, instance):
        for field in instance._meta.concrete_fields:
            if not isinstance(field, models.ForeignKey):
                continue
            if not issubclass(field.remote_field.model, BaseModel):
                continue
            related = getattr(instance, field.name, None)
            if related is not None and related.is_deleted:
                return None
        return super().to_representation(instance)


class LoreSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoreSource
        fields = ('id', 'title', 'source_type', 'url', 'citation', 'notes')
        read_only_fields = fields


class LoreMetadataModelSerializer(serializers.ModelSerializer):
    """Add shared lore provenance fields to every BaseModel representation."""

    def get_field_names(self, declared_fields, info):
        field_names = list(super().get_field_names(declared_fields, info))
        model = self.Meta.model
        if isinstance(model, type) and issubclass(model, BaseModel):
            for field_name in ('lore_accuracy', 'lore_notes', 'lore_sources'):
                if field_name not in field_names:
                    field_names.append(field_name)
        return field_names

    def build_relational_field(self, field_name, relation_info):
        if field_name == 'lore_sources':
            return LoreSourceSerializer, {'many': True, 'read_only': True}
        return super().build_relational_field(field_name, relation_info)

    def to_representation(self, instance):
        if instance is None:
            return None
        if isinstance(instance, BaseModel) and instance.is_deleted:
            return None

        representation = super().to_representation(instance)
        deleted_foreign_keys = {}
        for model_field in instance._meta.concrete_fields:
            if not isinstance(model_field, models.ForeignKey):
                continue
            related_model = model_field.remote_field.model
            if not issubclass(related_model, BaseModel):
                continue
            related = getattr(instance, model_field.name, None)
            if related is not None and related.is_deleted:
                deleted_foreign_keys[model_field.name] = related

        for field_name, field in self.fields.items():
            if isinstance(field, serializers.RelatedField):
                related = field.get_attribute(instance)
                if isinstance(related, BaseModel) and related.is_deleted:
                    representation[field_name] = None
            if not isinstance(field, serializers.SerializerMethodField):
                continue
            value = representation.get(field_name)
            if field_name.endswith('_slug'):
                relation_prefix = field_name.removesuffix('_slug')
                for related_name, related in deleted_foreign_keys.items():
                    if (
                        related_name == relation_prefix
                        or related_name.startswith(f'{relation_prefix}_')
                    ) and value == related.slug:
                        representation[field_name] = None
                        break
            if isinstance(value, dict) and value.get('type') and value.get('slug'):
                for related in deleted_foreign_keys.values():
                    if value['type'] == related._meta.model_name and value['slug'] == related.slug:
                        representation[field_name] = None
                        break
        for field_name, value in representation.items():
            if isinstance(value, list):
                representation[field_name] = [item for item in value if item is not None]
        return representation
