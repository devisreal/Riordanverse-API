from rest_framework import serializers

from apps.characters.models import Character, Power
from apps.images.serializers import ImageListSerializer


def _primary_image(character):
    link = next(
        (image_link for image_link in character.images.all() if image_link.is_primary), None
    )
    return ImageListSerializer(link.image).data if link else None


class PowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Power
        fields = ('id', 'name', 'description', 'source', 'scope', 'limitations')


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
            'primary_image',
        )

    def get_primary_image(self, obj):
        return _primary_image(obj)

    def get_divine_parent_slug(self, obj):
        return obj.divine_parent.slug if obj.divine_parent else None


class CharacterDetailSerializer(serializers.ModelSerializer):
    """Full detail representation for a single character."""

    primary_image = serializers.SerializerMethodField()
    powers = PowerSerializer(many=True, read_only=True)
    divine_parent_slug = serializers.SerializerMethodField()
    mortal_parent_ref_slug = serializers.SerializerMethodField()
    sibling_slugs = serializers.SerializerMethodField()
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
            'divine_parent_slug',
            'mortal_parent_name',
            'mortal_parent_ref_slug',
            'sibling_slugs',
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

    def get_divine_parent_slug(self, obj):
        return obj.divine_parent.slug if obj.divine_parent else None

    def get_mortal_parent_ref_slug(self, obj):
        return obj.mortal_parent_ref.slug if obj.mortal_parent_ref else None

    def get_sibling_slugs(self, obj):
        return [sibling.slug for sibling in obj.siblings.all()]

    def get_empathy_link_slug(self, obj):
        return obj.empathy_link.slug if obj.empathy_link else None

    def get_weapon_slugs(self, obj):
        return [weapon.slug for weapon in obj.weapons.all()]

    def get_first_appearance_book_slug(self, obj):
        return obj.first_appearance_book.slug if obj.first_appearance_book else None

    def get_books_appeared_in_slugs(self, obj):
        return [book.slug for book in obj.books_appeared_in.all()]
