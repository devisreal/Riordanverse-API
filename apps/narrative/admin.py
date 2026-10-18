from django.contrib import admin

from apps.narrative.models import Book, BookImage, Event, Prophecy, Quest


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


@admin.register(Prophecy)
class ProphecyAdmin(admin.ModelAdmin):
    list_display = ('title', 'oracle_type', 'delivered_by', 'fulfilled_in')
    search_fields = ('title', 'text', 'interpretation_notes')
    raw_id_fields = ('delivered_by', 'fulfilled_in')
    filter_horizontal = ('subject', 'books_relevant_to')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ('title', 'book', 'led_by', 'initiated_by')
    list_filter = ('book',)
    search_fields = ('title', 'objective', 'outcome', 'description')
    raw_id_fields = ('book', 'led_by', 'prophecy')
    filter_horizontal = (
        'participants',
        'casualties',
        'locations_visited',
        'monsters_encountered',
        'items_recovered',
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'book', 'location')
    list_filter = ('event_type', 'book')
    search_fields = ('name', 'outcome', 'significance', 'description')
    raw_id_fields = ('book', 'location')
    filter_horizontal = (
        'participant_characters',
        'participant_gods',
        'participant_titans',
        'participant_monsters',
        'casualties',
    )
    readonly_fields = ('created_at', 'updated_at')
