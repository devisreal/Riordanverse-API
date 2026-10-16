# ruff: noqa: RUF012

from rest_framework import serializers

from apps.divinities.models import God, Titan
from apps.images.serializers import ImageListSerializer


def _flatten_relationship(rel, direction='to'):
    """
    Flatten a DivineRelationship row into a clean dict for API consumers.
    direction: "to" returns the target entity; "from" returns the source.
    """
    if direction == 'to':
        entity = rel.to_god or rel.to_titan
        entity_type = 'god' if rel.to_god else 'titan'
    else:
        entity = rel.from_god or rel.from_titan
        entity_type = 'god' if rel.from_god else 'titan'

    return {
        'type': entity_type,
        'slug': entity.slug,
        'name': entity.name,
        'relationship': rel.relationship_type,
    }


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
        rels = obj.relationships_as_to.filter(relationship_type='parent_of').select_related(
            'from_god', 'from_titan'
        )
        return [_flatten_relationship(r, direction='from') for r in rels]

    def get_siblings(self, obj):
        rels = obj.relationships_as_to.filter(relationship_type='sibling_of').select_related(
            'from_god', 'from_titan'
        )
        return [_flatten_relationship(r, direction='from') for r in rels]

    def get_consorts(self, obj):
        rels = obj.relationships_as_from.filter(relationship_type='consort_of').select_related(
            'to_god', 'to_titan'
        )
        return [_flatten_relationship(r, direction='to') for r in rels]

    def get_children(self, obj):
        rels = obj.relationships_as_from.filter(relationship_type='parent_of').select_related(
            'to_god', 'to_titan'
        )
        return [_flatten_relationship(r, direction='to') for r in rels]

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
            'generation',
            'status',
            'alignment',
            'alignment_display',
            'domains',
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
    first_appearance_book_slug = serializers.SerializerMethodField()
    books_appeared_in_slugs = serializers.SerializerMethodField()

    class Meta:
        model = Titan
        fields = [
            'id',
            'slug',
            'name',
            'mythology',
            'generation',
            'generation_display',
            'status',
            'status_display',
            'alignment',
            'alignment_display',
            'domains',
            'weapon_or_power',
            'role_in_series',
            'prison_location',
            'description',
            'parents',
            'siblings',
            'children',
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
        rels = obj.relationships_as_to.filter(relationship_type='parent_of').select_related(
            'from_god', 'from_titan'
        )
        return [_flatten_relationship(r, direction='from') for r in rels]

    def get_siblings(self, obj):
        rels = obj.relationships_as_to.filter(relationship_type='sibling_of').select_related(
            'from_god', 'from_titan'
        )
        return [_flatten_relationship(r, direction='from') for r in rels]

    def get_children(self, obj):
        rels = obj.relationships_as_from.filter(relationship_type='parent_of').select_related(
            'to_god', 'to_titan'
        )
        return [_flatten_relationship(r, direction='to') for r in rels]

    def get_first_appearance_book_slug(self, obj):
        return obj.first_appearance_book.slug if obj.first_appearance_book else None

    def get_books_appeared_in_slugs(self, obj):
        return list(obj.books_appeared_in.values_list('slug', flat=True))
