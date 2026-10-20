# ruff: noqa: RUF012

from django.db.models import Q
from rest_framework import serializers

from apps.characters.models import Character
from apps.divinities.models import DivineRelationship, God, Titan
from apps.images.serializers import ImageListSerializer


def _relationship_filters(obj):
    if isinstance(obj, God):
        return Q(from_god=obj), Q(to_god=obj)
    if isinstance(obj, Titan):
        return Q(from_titan=obj), Q(to_titan=obj)
    return Q(from_character=obj), Q(to_character=obj)


def _relationship_entity(rel, side):
    if side == 'from':
        entity = rel.from_god or rel.from_titan or rel.from_character
    else:
        entity = rel.to_god or rel.to_titan or rel.to_character
    entity_type = (
        'god'
        if isinstance(entity, God)
        else 'titan'
        if isinstance(entity, Titan)
        else 'character'
        if isinstance(entity, Character)
        else 'unknown'
    )
    return {
        'type': entity_type,
        'slug': entity.slug,
        'name': entity.name,
        'relationship': rel.relationship_type,
    }


def _is_from_entity(rel, obj):
    if isinstance(obj, God):
        return rel.from_god_id == obj.pk
    if isinstance(obj, Titan):
        return rel.from_titan_id == obj.pk
    return rel.from_character_id == obj.pk


def _serialize_entity_relationships(obj, category):
    from_filter, to_filter = _relationship_filters(obj)
    related_filters = {
        'parents': (Q(relationship_type='parent_of') & to_filter)
        | (Q(relationship_type='child_of') & from_filter),
        'children': (Q(relationship_type='parent_of') & from_filter)
        | (Q(relationship_type='child_of') & to_filter),
        'siblings': Q(relationship_type='sibling_of') & (from_filter | to_filter),
        'consorts': Q(relationship_type='consort_of') & (from_filter | to_filter),
    }
    relationships = DivineRelationship.objects.filter(related_filters[category]).select_related(
        'from_god', 'from_titan', 'from_character', 'to_god', 'to_titan', 'to_character'
    )

    results = []
    seen = set()
    for rel in relationships:
        if category == 'parents':
            side = 'from' if rel.relationship_type == 'parent_of' else 'to'
        elif category == 'children':
            side = 'to' if rel.relationship_type == 'parent_of' else 'from'
        else:
            side = 'to' if _is_from_entity(rel, obj) else 'from'

        result = _relationship_entity(rel, side)
        key = (result['type'], result['slug'])
        if key not in seen:
            results.append(result)
            seen.add(key)
    return results


class GodListSerializer(serializers.ModelSerializer):
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
            'primary_image',
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).select_related('image').first()
        return ImageListSerializer(primary.image).data if primary else None


class GodDetailSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    tier_display = serializers.CharField(source='get_tier_display', read_only=True)
    affiliation_display = serializers.CharField(source='get_affiliation_display', read_only=True)
    oath_status_display = serializers.CharField(source='get_oath_status_display', read_only=True)
    parents = serializers.SerializerMethodField()
    siblings = serializers.SerializerMethodField()
    consorts = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    children_demigod_slugs = serializers.SerializerMethodField()
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
            'parents',
            'siblings',
            'consorts',
            'children',
            'children_demigod_slugs',
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

    def get_parents(self, obj):
        return _serialize_entity_relationships(obj, 'parents')

    def get_siblings(self, obj):
        return _serialize_entity_relationships(obj, 'siblings')

    def get_consorts(self, obj):
        return _serialize_entity_relationships(obj, 'consorts')

    def get_children(self, obj):
        return _serialize_entity_relationships(obj, 'children')

    def get_children_demigod_slugs(self, obj):
        return list(obj.children_demigods.values_list('slug', flat=True))

    def get_weapon_slugs(self, obj):
        return list(obj.weapons.values_list('slug', flat=True))

    def get_first_appearance_book_slug(self, obj):
        return obj.first_appearance_book.slug if obj.first_appearance_book else None

    def get_books_appeared_in_slugs(self, obj):
        return list(obj.books_appeared_in.values_list('slug', flat=True))


class TitanListSerializer(serializers.ModelSerializer):
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
            'primary_image',
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).select_related('image').first()
        return ImageListSerializer(primary.image).data if primary else None


class TitanDetailSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    alignment_display = serializers.CharField(source='get_alignment_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    generation_display = serializers.CharField(source='get_generation_display', read_only=True)
    parents = serializers.SerializerMethodField()
    siblings = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    consorts = serializers.SerializerMethodField()
    first_appearance_book_slug = serializers.SerializerMethodField()
    books_appeared_in_slugs = serializers.SerializerMethodField()

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
            'weapon_or_power',
            'role_in_series',
            'prison_location',
            'description',
            'parents',
            'siblings',
            'children',
            'consorts',
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

    def get_parents(self, obj):
        return _serialize_entity_relationships(obj, 'parents')

    def get_siblings(self, obj):
        return _serialize_entity_relationships(obj, 'siblings')

    def get_children(self, obj):
        return _serialize_entity_relationships(obj, 'children')

    def get_consorts(self, obj):
        return _serialize_entity_relationships(obj, 'consorts')

    def get_first_appearance_book_slug(self, obj):
        return obj.first_appearance_book.slug if obj.first_appearance_book else None

    def get_books_appeared_in_slugs(self, obj):
        return list(obj.books_appeared_in.values_list('slug', flat=True))
