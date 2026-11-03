# ruff: noqa: RUF012

from django.contrib import admin

from apps.core.admin import SoftDeleteAdminMixin
from apps.locations.models import Location, LocationImage


class LocationImageInline(admin.TabularInline):
    model = LocationImage
    extra = 1
    fields = ('image', 'is_primary', 'display_order')
    ordering = ('display_order',)


@admin.register(Location)
class LocationAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'location_type',
        'real_world_location',
        'is_hidden_from_mortals',
    )
    list_filter = ('location_type', 'is_hidden_from_mortals')
    search_fields = ('name', 'description', 'real_world_location', 'mythological_significance')
    raw_id_fields = (
        'controlled_by_god',
        'controlled_by_titan',
        'controlled_by_character',
        'controlled_by_monster',
    )
    filter_horizontal = ('books_appeared_in',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [LocationImageInline]
