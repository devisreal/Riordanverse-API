from django.contrib import admin

from apps.organizations.models import Cabin, Faction


@admin.register(Cabin)
class CabinAdmin(admin.ModelAdmin):
    list_display = (
        'number',
        'deity',
        'is_honorary',
        'is_empty',
        'head_counselor',
        'position',
    )
    list_filter = ('is_honorary', 'is_empty', 'position')
    search_fields = ('architecture_description', 'deity__name')
    raw_id_fields = ('deity', 'head_counselor', 'added_in_book')
    filter_horizontal = ('known_campers',)
    readonly_fields = ('slug', 'created_at', 'updated_at')


@admin.register(Faction)
class FactionAdmin(admin.ModelAdmin):
    list_display = ('name', 'faction_type', 'alignment')
    list_filter = ('faction_type', 'alignment')
    search_fields = ('name', 'description')
    raw_id_fields = ('leader_character', 'leader_god')
    filter_horizontal = ('members', 'books_active_in')
    readonly_fields = ('created_at', 'updated_at')
