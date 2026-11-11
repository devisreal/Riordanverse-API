# ruff: noqa: RUF012

from django.contrib import admin

from apps.characters.models import Character, CharacterImage, Power
from apps.core.admin import SoftDeleteAdminMixin


class PowerInline(admin.TabularInline):
    model = Power
    extra = 1
    fields = (
        'name',
        'wiki_url',
        'source',
        'type',
        'is_passive',
        'is_book_specific',
        'first_demonstrated_book',
        'display_order',
        'description',
        'scope',
        'limitations',
    )


class CharacterImageInline(admin.TabularInline):
    model = CharacterImage
    extra = 1
    fields = ('image', 'is_primary', 'display_order')
    ordering = ('display_order',)


@admin.register(Character)
class CharacterAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'character_type',
        'species',
        'status',
        'is_demigod',
        'is_big_three_child',
        'cabin_number',
    )
    list_filter = (
        'character_type',
        'species',
        'status',
        'is_demigod',
        'is_big_three_child',
        'is_hunter_of_artemis',
        'is_oracle',
        'is_possessed',
        'can_see_through_mist',
    )
    search_fields = ('name', 'description', 'lore_notes')
    filter_horizontal = ('siblings', 'weapons', 'books_appeared_in')
    raw_id_fields = ('divine_parent', 'mortal_parent_ref', 'empathy_link', 'first_appearance_book')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PowerInline, CharacterImageInline]


@admin.register(Power)
class PowerAdmin(admin.ModelAdmin):
    list_display = ('name', 'character', 'source', 'type', 'is_passive', 'display_order')
    list_filter = ('source', 'type', 'is_passive', 'is_book_specific')
    search_fields = ('name', 'description', 'character__name')
    raw_id_fields = ('character', 'first_demonstrated_book')
