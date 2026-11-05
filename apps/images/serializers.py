from rest_framework import serializers

from apps.images.models import Image


class ImageSerializer(serializers.ModelSerializer):
    """Full image detail for gallery responses."""

    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Image
        fields = (
            'id',
            'url',
            'thumbnail_url',
            'alt_text',
            'source_type',
            'source_type_display',
            'category',
            'category_display',
            'artist_name',
            'artist_url',
            'source_url',
            'license',
            'license_url',
            'width',
            'height',
            'file_format',
            'wiki_url',
            'uploaded_at',
        )


class ImageListSerializer(serializers.ModelSerializer):
    """Compact image representation for embedding in entity list responses."""

    class Meta:
        model = Image
        fields = (
            'id',
            'url',
            'thumbnail_url',
            'alt_text',
            'source_type',
            'category',
            'artist_name',
            'artist_url',
            'source_url',
            'license',
            'license_url',
            'wiki_url',
        )
