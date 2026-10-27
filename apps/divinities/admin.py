# ruff: noqa: RUF012

from django.contrib import admin

from apps.divinities.models import (
    DivineRelationship,
    God,
    GodImage,
    Titan,
    TitanImage,
)


class GodImageInline(admin.TabularInline):
    model = GodImage
    extra = 1
    fields = ('image', 'is_primary', 'display_order')
    ordering = ('display_order',)


class TitanImageInline(admin.TabularInline):
    model = TitanImage
    extra = 1
    fields = ('image', 'is_primary', 'display_order')
    ordering = ('display_order',)


@admin.register(God)
class GodAdmin(admin.ModelAdmin):
    list_display = ('name', 'roman_name', 'tier', 'affiliation', 'is_big_three', 'has_cabin')
    list_filter = ('tier', 'affiliation', 'is_big_three', 'roman_only', 'mythology')
    search_fields = ('name', 'roman_name', 'description')
    filter_horizontal = ('children_demigods', 'weapons', 'books_appeared_in')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [GodImageInline]


@admin.register(Titan)
class TitanAdmin(admin.ModelAdmin):
    list_display = ('name', 'generation', 'status', 'alignment')
    list_filter = ('generation', 'status', 'alignment', 'mythology')
    search_fields = ('name', 'description', 'role_in_series')
    filter_horizontal = ('books_appeared_in', 'weapons')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TitanImageInline]


@admin.register(DivineRelationship)
class DivineRelationshipAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'relationship_type')
    list_filter = ('relationship_type',)
    raw_id_fields = (
        'from_god',
        'from_titan',
        'from_character',
        'from_monster',
        'from_creature',
        'to_god',
        'to_titan',
        'to_character',
        'to_monster',
        'to_creature',
    )
