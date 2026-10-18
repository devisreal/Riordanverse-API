# ruff: noqa: RUF012

from rest_framework import serializers

from apps.organizations.models import Cabin, Faction


class CabinListSerializer(serializers.ModelSerializer):
    """Lightweight — for list views."""

    deity_slug = serializers.SerializerMethodField()
    deity_name = serializers.SerializerMethodField()
    position_display = serializers.CharField(source='get_position_display', read_only=True)

    class Meta:
        model = Cabin
        fields = [
            'id',
            'slug',
            'number',
            'deity_slug',
            'deity_name',
            'is_honorary',
            'is_empty',
            'position',
            'position_display',
        ]

    def get_deity_slug(self, obj):
        return obj.deity.slug if obj.deity else None

    def get_deity_name(self, obj):
        return obj.deity.name if obj.deity else None


class CabinDetailSerializer(serializers.ModelSerializer):
    """Full detail — for single cabin retrieval."""

    deity_slug = serializers.SerializerMethodField()
    deity_name = serializers.SerializerMethodField()
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    head_counselor_slug = serializers.SerializerMethodField()
    known_camper_slugs = serializers.SerializerMethodField()
    added_in_book_slug = serializers.SerializerMethodField()

    class Meta:
        model = Cabin
        fields = [
            'id',
            'slug',
            'number',
            'deity_slug',
            'deity_name',
            'is_honorary',
            'is_empty',
            'architecture_description',
            'position',
            'position_display',
            'head_counselor_slug',
            'known_camper_slugs',
            'added_in_book_slug',
            'wiki_url',
            'created_at',
            'updated_at',
        ]

    def get_deity_slug(self, obj):
        return obj.deity.slug if obj.deity else None

    def get_deity_name(self, obj):
        return obj.deity.name if obj.deity else None

    def get_head_counselor_slug(self, obj):
        return obj.head_counselor.slug if obj.head_counselor else None

    def get_known_camper_slugs(self, obj):
        return list(obj.known_campers.values_list('slug', flat=True))

    def get_added_in_book_slug(self, obj):
        return obj.added_in_book.slug if obj.added_in_book else None


class FactionListSerializer(serializers.ModelSerializer):
    """Lightweight — for list views."""

    faction_type_display = serializers.CharField(source='get_faction_type_display', read_only=True)
    alignment_display = serializers.CharField(source='get_alignment_display', read_only=True)
    leader = serializers.SerializerMethodField()

    class Meta:
        model = Faction
        fields = [
            'id',
            'slug',
            'name',
            'faction_type',
            'faction_type_display',
            'alignment',
            'alignment_display',
            'leader',
        ]

    def get_leader(self, obj):
        if obj.leader_character:
            return {
                'type': 'character',
                'slug': obj.leader_character.slug,
                'name': obj.leader_character.name,
            }
        if obj.leader_god:
            return {
                'type': 'god',
                'slug': obj.leader_god.slug,
                'name': obj.leader_god.name,
            }
        return None


class FactionDetailSerializer(serializers.ModelSerializer):
    """Full detail — for single faction retrieval."""

    faction_type_display = serializers.CharField(source='get_faction_type_display', read_only=True)
    alignment_display = serializers.CharField(source='get_alignment_display', read_only=True)
    leader = serializers.SerializerMethodField()
    member_slugs = serializers.SerializerMethodField()
    books_active_in_slugs = serializers.SerializerMethodField()

    class Meta:
        model = Faction
        fields = [
            'id',
            'slug',
            'name',
            'faction_type',
            'faction_type_display',
            'alignment',
            'alignment_display',
            'leader',
            'member_slugs',
            'books_active_in_slugs',
            'description',
            'wiki_url',
            'created_at',
            'updated_at',
        ]

    def get_leader(self, obj):
        if obj.leader_character:
            return {
                'type': 'character',
                'slug': obj.leader_character.slug,
                'name': obj.leader_character.name,
            }
        if obj.leader_god:
            return {
                'type': 'god',
                'slug': obj.leader_god.slug,
                'name': obj.leader_god.name,
            }
        return None

    def get_member_slugs(self, obj):
        return list(obj.members.values_list('slug', flat=True))

    def get_books_active_in_slugs(self, obj):
        return list(obj.books_active_in.values_list('slug', flat=True))
