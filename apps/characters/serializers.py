from rest_framework import serializers

from apps.characters.models import Character, Power
from apps.divinities.family import serialize_family
from apps.images.serializers import ImageListSerializer


def _primary_image(character):
    link = next(
        (image_link for image_link in character.images.all() if image_link.is_primary), None
    )
    return ImageListSerializer(link.image).data if link else None


class PowerSerializer(serializers.ModelSerializer):
    first_demonstrated_book = serializers.SlugRelatedField(read_only=True, slug_field='slug')

    class Meta:
        model = Power
        fields = (
            'id',
            'name',
            'wiki_url',
            'description',
            'source',
            'type',
            'scope',
            'limitations',
            'is_passive',
            'is_book_specific',
            'first_demonstrated_book',
            'display_order',
        )


class CharacterListSerializer(serializers.ModelSerializer):
    """Lightweight representation for collection responses and embedding."""

    primary_image = serializers.SerializerMethodField()
    divine_parent_slug = serializers.SerializerMethodField()
    character_type = serializers.CharField(source='get_character_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Character
        fields = (
            'id',
            'slug',
            'name',
            'aliases',
            'character_type',
            'species',
            'status',
            'status_display',
            'is_demigod',
            'is_big_three_child',
            'divine_parent_slug',
            'cabin_number',
            'wiki_url',
            'primary_image',
        )

    def get_primary_image(self, obj):
        return _primary_image(obj)

    def get_divine_parent_slug(self, obj):
        parent = obj.divine_parent or obj.divine_parent_titan
        return parent.slug if parent else None


class CharacterDetailSerializer(serializers.ModelSerializer):
    """Full detail representation for a single character."""

    primary_image = serializers.SerializerMethodField()
    powers = PowerSerializer(many=True, read_only=True)
    type = serializers.SerializerMethodField()
    family = serializers.SerializerMethodField()
    empathy_link_slug = serializers.SerializerMethodField()
    weapon_slugs = serializers.SerializerMethodField()
    first_appearance_book_slug = serializers.SerializerMethodField()
    books_appeared_in_slugs = serializers.SerializerMethodField()
    character_type_display = serializers.CharField(
        source='get_character_type_display', read_only=True
    )
    species_display = serializers.CharField(source='get_species_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    greek_or_roman_display = serializers.CharField(
        source='get_greek_or_roman_display', read_only=True
    )

    class Meta:
        model = Character
        fields = (
            'id',
            'slug',
            'name',
            'aliases',
            'character_type',
            'character_type_display',
            'species',
            'species_display',
            'gender',
            'gender_display',
            'status',
            'status_display',
            'greek_or_roman',
            'greek_or_roman_display',
            'age_first_appearance',
            'type',
            'family',
            'empathy_link_slug',
            'cabin_number',
            'affiliation',
            'fatal_flaw',
            'powers',
            'weapon_slugs',
            'can_see_through_mist',
            'has_adhd',
            'has_dyslexia',
            'is_demigod',
            'is_big_three_child',
            'is_hunter_of_artemis',
            'is_oracle',
            'is_possessed',
            'appearance',
            'personality_traits',
            'special_states',
            'quote',
            'description',
            'lore_notes',
            'first_appearance_book_slug',
            'books_appeared_in_slugs',
            'primary_image',
            'wiki_url',
            'created_at',
            'updated_at',
        )

    def get_primary_image(self, obj):
        return _primary_image(obj)

    def get_type(self, obj):
        return 'character'

    def get_family(self, obj):
        return serialize_family(obj)

    def get_empathy_link_slug(self, obj):
        return obj.empathy_link.slug if obj.empathy_link else None

    def get_weapon_slugs(self, obj):
        return [weapon.slug for weapon in obj.weapons.all()]

    def get_first_appearance_book_slug(self, obj):
        return obj.first_appearance_book.slug if obj.first_appearance_book else None

    def get_books_appeared_in_slugs(self, obj):
        return [book.slug for book in obj.books_appeared_in.all()]
