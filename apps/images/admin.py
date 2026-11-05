from django.contrib import admin

from apps.images.models import Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'source_type',
        'category',
        'artist_name',
        'license',
        'license_url',
        'uploaded_at',
    )
    list_filter = ('source_type', 'category')
    search_fields = ('alt_text', 'artist_name', 'license', 'license_url', 'url')
    readonly_fields = ('uploaded_at',)
