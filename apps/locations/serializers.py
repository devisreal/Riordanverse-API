# ruff: noqa: RUF012

from rest_framework import serializers

from apps.images.serializers import ImageListSerializer
from apps.locations.models import Location


class LocationListSerializer(serializers.ModelSerializer):
    """Lightweight — for list views."""

    primary_image = serializers.SerializerMethodField()
    location_type_display = serializers.CharField(
        source='get_location_type_display', read_only=True
    )
    controlled_by = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            'id',
            'slug',
            'name',
            'location_type',
            'location_type_display',
            'real_world_location',
            'is_hidden_from_mortals',
            'controlled_by',
            'wiki_url',
            'primary_image',
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).select_related('image').first()
        return ImageListSerializer(primary.image).data if primary else None

    def get_controlled_by(self, obj):
        if obj.controlled_by_god:
            return {
                'type': 'god',
                'slug': obj.controlled_by_god.slug,
                'name': obj.controlled_by_god.name,
            }
        if obj.controlled_by_titan:
            return {
                'type': 'titan',
                'slug': obj.controlled_by_titan.slug,
                'name': obj.controlled_by_titan.name,
            }
        if obj.controlled_by_character:
            return {
                'type': 'character',
                'slug': obj.controlled_by_character.slug,
                'name': obj.controlled_by_character.name,
            }
        if obj.controlled_by_monster:
            return {
                'type': 'monster',
                'slug': obj.controlled_by_monster.slug,
                'name': obj.controlled_by_monster.name,
            }
        return None


class LocationDetailSerializer(serializers.ModelSerializer):
    """Full detail — for single location retrieval."""

    primary_image = serializers.SerializerMethodField()
    location_type_display = serializers.CharField(
        source='get_location_type_display', read_only=True
    )
    controlled_by = serializers.SerializerMethodField()
    books_appeared_in_slugs = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            'id',
            'slug',
            'name',
            'location_type',
            'location_type_display',
            'real_world_location',
            'mythological_significance',
            'is_hidden_from_mortals',
            'coordinates_approx',
            'notable_events',
            'controlled_by',
            'description',
            'books_appeared_in_slugs',
            'primary_image',
            'wiki_url',
            'created_at',
            'updated_at',
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).select_related('image').first()
        return ImageListSerializer(primary.image).data if primary else None

    def get_controlled_by(self, obj):
        if obj.controlled_by_god:
            return {
                'type': 'god',
                'slug': obj.controlled_by_god.slug,
                'name': obj.controlled_by_god.name,
            }
        if obj.controlled_by_titan:
            return {
                'type': 'titan',
                'slug': obj.controlled_by_titan.slug,
                'name': obj.controlled_by_titan.name,
            }
        if obj.controlled_by_character:
            return {
                'type': 'character',
                'slug': obj.controlled_by_character.slug,
                'name': obj.controlled_by_character.name,
            }
        if obj.controlled_by_monster:
            return {
                'type': 'monster',
                'slug': obj.controlled_by_monster.slug,
                'name': obj.controlled_by_monster.name,
            }
        return None

    def get_books_appeared_in_slugs(self, obj):
        return list(obj.books_appeared_in.values_list('slug', flat=True))
