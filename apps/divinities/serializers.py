# ruff: noqa: RUF012

from rest_framework import serializers

from apps.core.serializers import LoreMetadataModelSerializer
from apps.divinities.family import serialize_family
from apps.divinities.models import God, Titan
from apps.images.serializers import ImageListSerializer


class GodListSerializer(LoreMetadataModelSerializer):
    primary_image = serializers.SerializerMethodField()
    tier_display = serializers.CharField(source='get_tier_display', read_only=True)

    class Meta:
        model = God
        fields = [
            'id',
            'slug',
            'name',
            'roman_name',
            'tier',
            'tier_display',
            'domains',
            'is_big_three',
            'has_cabin',
            'cabin_number',
            'wiki_url',
            'primary_image',
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).select_related('image').first()
        return ImageListSerializer(primary.image).data if primary else None


class GodDetailSerializer(LoreMetadataModelSerializer):
    primary_image = serializers.SerializerMethodField()
    tier_display = serializers.CharField(source='get_tier_display', read_only=True)
    affiliation_display = serializers.CharField(source='get_affiliation_display', read_only=True)
    oath_status_display = serializers.CharField(source='get_oath_status_display', read_only=True)
    type = serializers.SerializerMethodField()
    family = serializers.SerializerMethodField()
    weapon_slugs = serializers.SerializerMethodField()
    first_appearance_book_slug = serializers.SerializerMethodField()
    books_appeared_in_slugs = serializers.SerializerMethodField()

    class Meta:
        model = God
        fields = [
            'id',
            'slug',
            'name',
            'roman_name',
            'mythology',
            'tier',
            'tier_display',
            'affiliation',
            'affiliation_display',
            'status',
            'domains',
            'symbols',
            'sacred_animals',
            'sacred_plants',
            'sacred_items',
            'cabin_number',
            'has_cabin',
            'is_big_three',
            'oath_status',
            'oath_status_display',
            'greek_aspect_personality',
            'roman_aspect_personality',
            'roman_only',
            'home',
            'description',
            'type',
            'family',
            'weapon_slugs',
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

    def get_type(self, obj):
        return 'god'

    def get_family(self, obj):
        return serialize_family(obj)

    def get_weapon_slugs(self, obj):
        return list(obj.weapons.values_list('slug', flat=True))

    def get_first_appearance_book_slug(self, obj):
        return obj.first_appearance_book.slug if obj.first_appearance_book else None

    def get_books_appeared_in_slugs(self, obj):
        return list(obj.books_appeared_in.values_list('slug', flat=True))


class TitanListSerializer(LoreMetadataModelSerializer):
    primary_image = serializers.SerializerMethodField()
    alignment_display = serializers.CharField(source='get_alignment_display', read_only=True)

    class Meta:
        model = Titan
        fields = [
            'id',
            'slug',
            'name',
            'roman_name',
            'generation',
            'status',
            'alignment',
            'alignment_display',
            'domains',
            'symbols',
            'sacred_animals',
            'sacred_plants',
            'wiki_url',
            'primary_image',
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).select_related('image').first()
        return ImageListSerializer(primary.image).data if primary else None


class TitanDetailSerializer(LoreMetadataModelSerializer):
    primary_image = serializers.SerializerMethodField()
    alignment_display = serializers.CharField(source='get_alignment_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    generation_display = serializers.CharField(source='get_generation_display', read_only=True)
    type = serializers.SerializerMethodField()
    family = serializers.SerializerMethodField()
    first_appearance_book_slug = serializers.SerializerMethodField()
    books_appeared_in_slugs = serializers.SerializerMethodField()
    weapon_slugs = serializers.SerializerMethodField()

    class Meta:
        model = Titan
        fields = [
            'id',
            'slug',
            'name',
            'roman_name',
            'mythology',
            'generation',
            'generation_display',
            'status',
            'status_display',
            'alignment',
            'alignment_display',
            'domains',
            'symbols',
            'sacred_animals',
            'sacred_plants',
            'weapon_or_power',
            'weapon_slugs',
            'home',
            'role_in_series',
            'prison_location',
            'description',
            'type',
            'family',
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

    def get_type(self, obj):
        return 'titan'

    def get_family(self, obj):
        return serialize_family(obj)

    def get_weapon_slugs(self, obj):
        return list(obj.weapons.values_list('slug', flat=True))

    def get_first_appearance_book_slug(self, obj):
        return obj.first_appearance_book.slug if obj.first_appearance_book else None

    def get_books_appeared_in_slugs(self, obj):
        return list(obj.books_appeared_in.values_list('slug', flat=True))
