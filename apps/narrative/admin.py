from django.contrib import admin

from apps.narrative.models import Book, BookImage


class BookImageInline(admin.TabularInline):
    model = BookImage
    extra = 1
    fields = ('image', 'is_primary', 'display_order')
    ordering = ('display_order',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'series', 'book_number', 'book_type', 'published_date')
    list_filter = ('series', 'book_type')
    search_fields = ('title', 'synopsis')
    filter_horizontal = ('main_characters', 'antagonists')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    inlines = (BookImageInline,)


@admin.register(BookImage)
class BookImageAdmin(admin.ModelAdmin):
    list_display = ('book', 'image', 'is_primary', 'display_order')
    list_filter = ('is_primary',)
    search_fields = ('book__title', 'image__alt_text', 'image__url')
