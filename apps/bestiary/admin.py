# ruff: noqa: RUF012

from django.contrib import admin

from apps.bestiary.models import Creature, Monster, MonsterDefeat, MonsterImage


class MonsterDefeatInline(admin.TabularInline):
    model = MonsterDefeat
    extra = 0
    fields = ('defeated_by', 'book', 'method', 'is_myth')
    ordering = ('id',)


@admin.register(MonsterDefeat)
class MonsterDefeatAdmin(admin.ModelAdmin):
    list_display = ('monster', 'defeated_by', 'book', 'method', 'is_myth')
    list_filter = ('is_myth', 'book')
    search_fields = ('monster__name', 'defeated_by__name', 'method')
    raw_id_fields = ('monster', 'defeated_by', 'book')
    list_select_related = ('monster', 'defeated_by', 'book')


class MonsterImageInline(admin.TabularInline):
    model = MonsterImage
    extra = 1
    fields = ('image', 'is_primary', 'display_order')
    ordering = ('display_order',)


@admin.register(Monster)
class MonsterAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'monster_type',
        'allegiance',
        'can_reform',
        'disguise_form',
    )
    list_filter = ('monster_type', 'allegiance', 'can_reform')
    search_fields = ('name', 'description', 'physical_description', 'disguise_form')
    filter_horizontal = ('defeated_by_gods', 'books_appeared_in')
    raw_id_fields = ('first_appearance_book',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MonsterDefeatInline, MonsterImageInline]


@admin.register(Creature)
class CreatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'alignment', 'habitat')
    list_filter = ('alignment',)
    search_fields = ('name', 'description', 'origin')
    filter_horizontal = ('notable_members',)
    readonly_fields = ('created_at', 'updated_at')
