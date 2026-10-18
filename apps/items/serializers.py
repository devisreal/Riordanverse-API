# ruff: noqa: RUF012

from rest_framework import serializers

from apps.images.serializers import ImageListSerializer
from apps.items.models import Weapon


class WeaponListSerializer(serializers.ModelSerializer):
    """Lightweight — for list views."""

    primary_image = serializers.SerializerMethodField()
    weapon_type_display = serializers.CharField(source='get_weapon_type_display', read_only=True)
    material_display = serializers.SerializerMethodField()
    owner_primary = serializers.SerializerMethodField()

    class Meta:
        model = Weapon
        fields = [
            'id',
            'slug',
            'name',
            'true_name',
            'weapon_type',
            'weapon_type_display',
            'material',
            'material_display',
            'transforms',
            'passes_through_mortals',
            'owner_primary',
            'primary_image',
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).select_related('image').first()
        return ImageListSerializer(primary.image).data if primary else None

    def get_material_display(self, obj):
        return obj.get_material_display() if obj.material else None

    def get_owner_primary(self, obj):
        if obj.owner_primary_character:
            return {
                'type': 'character',
                'slug': obj.owner_primary_character.slug,
                'name': obj.owner_primary_character.name,
            }
        if obj.owner_primary_god:
            return {
                'type': 'god',
                'slug': obj.owner_primary_god.slug,
                'name': obj.owner_primary_god.name,
            }
        return None


class WeaponDetailSerializer(serializers.ModelSerializer):
    """Full detail — for single weapon retrieval."""

    primary_image = serializers.SerializerMethodField()
    weapon_type_display = serializers.CharField(source='get_weapon_type_display', read_only=True)
    material_display = serializers.SerializerMethodField()
    owner_primary = serializers.SerializerMethodField()
    forged_by_slug = serializers.SerializerMethodField()
    first_appearance_book_slug = serializers.SerializerMethodField()
    books_appeared_in_slugs = serializers.SerializerMethodField()

    class Meta:
        model = Weapon
        fields = [
            'id',
            'slug',
            'name',
            'true_name',
            'weapon_type',
            'weapon_type_display',
            'material',
            'material_display',
            'form',
            'abilities',
            'transforms',
            'transform_trigger',
            'passes_through_mortals',
            'owner_primary',
            'owner_history',
            'forged_by_slug',
            'forged_by_notes',
            'origin_story',
            'description',
            'first_appearance_book_slug',
            'books_appeared_in_slugs',
            'primary_image',
            'wiki_url',
            'created_at',
            'updated_at',
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).select_related('image').first()
        return ImageListSerializer(primary.image).data if primary else None

    def get_material_display(self, obj):
        return obj.get_material_display() if obj.material else None

    def get_owner_primary(self, obj):
        if obj.owner_primary_character:
            return {
                'type': 'character',
                'slug': obj.owner_primary_character.slug,
                'name': obj.owner_primary_character.name,
            }
        if obj.owner_primary_god:
            return {
                'type': 'god',
                'slug': obj.owner_primary_god.slug,
                'name': obj.owner_primary_god.name,
            }
        return None

    def get_forged_by_slug(self, obj):
        return obj.forged_by.slug if obj.forged_by else None

    def get_first_appearance_book_slug(self, obj):
        return obj.first_appearance_book.slug if obj.first_appearance_book else None

    def get_books_appeared_in_slugs(self, obj):
        return list(obj.books_appeared_in.values_list('slug', flat=True))
