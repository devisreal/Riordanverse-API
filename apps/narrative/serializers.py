from rest_framework import serializers

from apps.images.serializers import ImageListSerializer
from apps.narrative.models import Book


def get_primary_image(book):
    link = next((image_link for image_link in book.images.all() if image_link.is_primary), None)
    return ImageListSerializer(link.image).data if link else None


class BookListSerializer(serializers.ModelSerializer):
    """Lightweight representation for book collection responses."""

    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = (
            'id',
            'slug',
            'title',
            'series',
            'book_number',
            'book_type',
            'published_date',
            'short_description',
            'camp_bead_description',
            'primary_image',
        )

    def get_primary_image(self, obj):
        return get_primary_image(obj)


class BookDetailSerializer(serializers.ModelSerializer):
    """Full representation for a single book."""

    primary_image = serializers.SerializerMethodField()
    narrator_slug = serializers.SerializerMethodField()
    main_character_slugs = serializers.SerializerMethodField()
    antagonist_slugs = serializers.SerializerMethodField()
    series_display = serializers.CharField(source='get_series_display', read_only=True)
    book_type_display = serializers.CharField(source='get_book_type_display', read_only=True)

    class Meta:
        model = Book
        fields = (
            'id',
            'slug',
            'title',
            'series',
            'series_display',
            'book_number',
            'book_type',
            'book_type_display',
            'published_date',
            'synopsis',
            'short_description',
            'camp_bead_description',
            'narrator_slug',
            'main_character_slugs',
            'antagonist_slugs',
            'primary_image',
            'wiki_url',
            'created_at',
            'updated_at',
        )

    def get_primary_image(self, obj):
        return get_primary_image(obj)

    def get_narrator_slug(self, obj):
        return obj.narrator.slug if obj.narrator else None

    def get_main_character_slugs(self, obj):
        return list(obj.main_characters.values_list('slug', flat=True))

    def get_antagonist_slugs(self, obj):
        return list(obj.antagonists.values_list('slug', flat=True))
