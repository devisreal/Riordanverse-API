# ruff: noqa: RUF012

from django.contrib import admin

from apps.core.admin import SoftDeleteAdminMixin
from apps.items.models import Weapon, WeaponImage


class WeaponImageInline(admin.TabularInline):
    model = WeaponImage
    extra = 1
    fields = ('image', 'is_primary', 'display_order')
    ordering = ('display_order',)


@admin.register(Weapon)
class WeaponAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'true_name',
        'weapon_type',
        'material',
        'transforms',
        'passes_through_mortals',
    )
    list_filter = ('weapon_type', 'material', 'transforms', 'passes_through_mortals')
    search_fields = ('name', 'true_name', 'description', 'origin_story')
    raw_id_fields = (
        'owner_primary_character',
        'owner_primary_god',
        'owner_primary_titan',
        'forged_by',
        'forged_by_character',
        'first_appearance_book',
    )
    filter_horizontal = ('books_appeared_in',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [WeaponImageInline]
