# ruff: noqa: RUF012

from rest_framework import serializers

from apps.bestiary.models import Creature, CreatureMember, Monster, MonsterDefeat
from apps.images.serializers import ImageListSerializer


class MonsterListSerializer(serializers.ModelSerializer):
    """Lightweight — for list views."""

    primary_image = serializers.SerializerMethodField()
    monster_type_display = serializers.CharField(source='get_monster_type_display', read_only=True)
    allegiance_display = serializers.CharField(source='get_allegiance_display', read_only=True)

    class Meta:
        model = Monster
        fields = [
            'id',
            'slug',
            'name',
            'aliases',
            'monster_type',
            'monster_type_display',
            'allegiance',
            'allegiance_display',
            'can_reform',
            'disguise_form',
            'wiki_url',
            'primary_image',
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).select_related('image').first()
        return ImageListSerializer(primary.image).data if primary else None


class MonsterDefeatSerializer(serializers.ModelSerializer):
    defeated_by = serializers.SlugRelatedField(read_only=True, slug_field='slug')
    book = serializers.SlugRelatedField(read_only=True, slug_field='slug', allow_null=True)

    class Meta:
        model = MonsterDefeat
        fields = ['defeated_by', 'book', 'method', 'is_myth']


class MonsterDetailSerializer(serializers.ModelSerializer):
    """Full detail — for single monster retrieval."""

    primary_image = serializers.SerializerMethodField()
    monster_type_display = serializers.CharField(source='get_monster_type_display', read_only=True)
    allegiance_display = serializers.CharField(source='get_allegiance_display', read_only=True)
    defeated_by_slugs = serializers.SerializerMethodField()
    defeated_by_god_slugs = serializers.SerializerMethodField()
    defeats = MonsterDefeatSerializer(many=True, read_only=True)
    first_appearance_book_slug = serializers.SerializerMethodField()
    books_appeared_in_slugs = serializers.SerializerMethodField()

    class Meta:
        model = Monster
        fields = [
            'id',
            'slug',
            'name',
            'aliases',
            'monster_type',
            'monster_type_display',
            'allegiance',
            'allegiance_display',
            'origin_myth',
            'physical_description',
            'abilities',
            'weaknesses',
            'notable_victims',
            'can_reform',
            'reform_time',
            'reform_location',
            'spoils_of_war',
            'parent_entity',
            'disguise_form',
            'defeated_by_slugs',
            'defeated_by_god_slugs',
            'defeats',
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

    def get_defeated_by_slugs(self, obj):
        return list(obj.defeated_by.values_list('slug', flat=True))

    def get_defeated_by_god_slugs(self, obj):
        return list(obj.defeated_by_gods.values_list('slug', flat=True))

    def get_first_appearance_book_slug(self, obj):
        return obj.first_appearance_book.slug if obj.first_appearance_book else None

    def get_books_appeared_in_slugs(self, obj):
        return list(obj.books_appeared_in.values_list('slug', flat=True))


class CreatureListSerializer(serializers.ModelSerializer):
    """Lightweight — for list views."""

    alignment_display = serializers.CharField(source='get_alignment_display', read_only=True)

    class Meta:
        model = Creature
        fields = [
            'id',
            'slug',
            'name',
            'alignment',
            'alignment_display',
            'habitat',
            'origin',
            'wiki_url',
        ]


class CreatureMemberSerializer(serializers.ModelSerializer):
    """Typed named member of a Creature species."""

    type = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = CreatureMember
        fields = ('type', 'slug', 'name')

    def _entity(self, obj):
        if obj.member_character_id:
            return 'character', obj.member_character
        if obj.member_monster_id:
            return 'monster', obj.member_monster
        return None, None

    def get_type(self, obj):
        return self._entity(obj)[0]

    def get_slug(self, obj):
        return self._entity(obj)[1].slug

    def get_name(self, obj):
        return self._entity(obj)[1].name


class CreatureDetailSerializer(serializers.ModelSerializer):
    """Full detail — for single creature/species retrieval."""

    alignment_display = serializers.CharField(source='get_alignment_display', read_only=True)
    notable_members = CreatureMemberSerializer(source='member_records', many=True, read_only=True)
    notable_member_slugs = serializers.SerializerMethodField()

    class Meta:
        model = Creature
        fields = [
            'id',
            'slug',
            'name',
            'description',
            'origin',
            'alignment',
            'alignment_display',
            'habitat',
            'abilities',
            'weaknesses',
            'notable_members',
            'notable_member_slugs',
            'wiki_url',
            'created_at',
            'updated_at',
        ]

    def get_notable_member_slugs(self, obj):
        return list(obj.notable_members.values_list('slug', flat=True))
