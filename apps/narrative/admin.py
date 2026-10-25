from django.contrib import admin

from apps.narrative.models import (
    Book,
    BookAntagonist,
    BookImage,
    BookMainCharacter,
    BookNarrator,
    Event,
    EventCasualty,
    Prophecy,
    ProphecySubject,
    Quest,
    QuestCasualty,
    QuestParticipant,
)


class BookImageInline(admin.TabularInline):
    model = BookImage
    extra = 1
    fields = ('image', 'is_primary', 'display_order')
    ordering = ('display_order',)


class BookNarratorInline(admin.TabularInline):
    model = BookNarrator
    extra = 0
    raw_id_fields = ('character', 'god', 'titan', 'monster', 'creature')


class BookMainCharacterInline(admin.TabularInline):
    model = BookMainCharacter
    extra = 0
    raw_id_fields = ('character', 'god', 'titan', 'monster', 'creature')


class BookAntagonistInline(admin.TabularInline):
    model = BookAntagonist
    extra = 0
    raw_id_fields = ('character', 'god', 'titan', 'monster', 'creature')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'series', 'book_number', 'book_type', 'published_date')
    list_filter = ('series', 'book_type')
    search_fields = ('title', 'synopsis')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    inlines = (
        BookImageInline,
        BookNarratorInline,
        BookMainCharacterInline,
        BookAntagonistInline,
    )


@admin.register(BookImage)
class BookImageAdmin(admin.ModelAdmin):
    list_display = ('book', 'image', 'is_primary', 'display_order')
    list_filter = ('is_primary',)
    search_fields = ('book__title', 'image__alt_text', 'image__url')


class ProphecySubjectInline(admin.TabularInline):
    model = ProphecySubject
    extra = 0
    raw_id_fields = ('subject_character', 'subject_god', 'subject_titan', 'subject_monster')


@admin.register(Prophecy)
class ProphecyAdmin(admin.ModelAdmin):
    list_display = ('title', 'oracle_type', 'delivered_by', 'fulfilled_in')
    search_fields = ('title', 'text', 'interpretation_notes')
    raw_id_fields = ('delivered_by', 'fulfilled_in')
    filter_horizontal = ('books_relevant_to',)
    inlines = (ProphecySubjectInline,)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProphecySubject)
class ProphecySubjectAdmin(admin.ModelAdmin):
    list_display = ('prophecy', 'subject_type', 'subject_display')
    search_fields = (
        'prophecy__title',
        'subject_character__name',
        'subject_god__name',
        'subject_titan__name',
        'subject_monster__name',
    )
    raw_id_fields = (
        'prophecy',
        'subject_character',
        'subject_god',
        'subject_titan',
        'subject_monster',
    )

    @admin.display(description='Entity type')
    def subject_type(self, obj):
        for subject_type in ('character', 'god', 'titan', 'monster'):
            if getattr(obj, f'subject_{subject_type}_id'):
                return subject_type
        return '—'

    @admin.display(description='Subject')
    def subject_display(self, obj):
        return obj.subject_character or obj.subject_god or obj.subject_titan or obj.subject_monster


class QuestParticipantInline(admin.TabularInline):
    model = QuestParticipant
    extra = 0
    raw_id_fields = (
        'participant_character',
        'participant_god',
        'participant_titan',
        'participant_monster',
    )


class QuestCasualtyInline(admin.TabularInline):
    model = QuestCasualty
    extra = 0
    raw_id_fields = ('casualty_character', 'casualty_god', 'casualty_titan', 'casualty_monster')


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ('title', 'book', 'led_by', 'initiated_by')
    list_filter = ('book',)
    search_fields = ('title', 'objective', 'outcome', 'description')
    raw_id_fields = ('book', 'led_by', 'prophecy')
    filter_horizontal = (
        'locations_visited',
        'monsters_encountered',
        'items_recovered',
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = (QuestParticipantInline, QuestCasualtyInline)


class EventCasualtyInline(admin.TabularInline):
    model = EventCasualty
    extra = 0
    raw_id_fields = ('casualty_character', 'casualty_god', 'casualty_titan', 'casualty_monster')


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
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = (EventCasualtyInline,)
