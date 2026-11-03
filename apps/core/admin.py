from django.contrib import admin, messages
from django.contrib.admin.widgets import FilteredSelectMultiple

from apps.core.models import LoreSource


class SoftDeleteAdminMixin:
    """Expose active and deleted lore records without offering hard deletion."""

    actions = ('soft_delete_selected', 'restore_selected')

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        for field in ('is_deleted', 'deleted_at'):
            if field not in fields:
                fields.append(field)
        return fields

    def get_queryset(self, request):
        queryset = self.model.all_objects.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            queryset = queryset.order_by(*ordering)
        return queryset

    def get_list_display(self, request):
        fields = list(super().get_list_display(request))
        for field in ('is_deleted', 'deleted_at'):
            if field not in fields:
                fields.append(field)
        return fields

    def get_list_filter(self, request):
        filters = list(super().get_list_filter(request))
        if 'is_deleted' not in filters:
            filters.append('is_deleted')
        return filters

    def has_delete_permission(self, request, obj=None):
        return False

    def delete_model(self, request, obj):
        obj.soft_delete()

    def delete_queryset(self, request, queryset):
        queryset.soft_delete()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'lore_sources':
            kwargs['widget'] = FilteredSelectMultiple('lore sources', is_stacked=False)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.action(description='Soft-delete selected lore records')
    def soft_delete_selected(self, request, queryset):
        deleted_count, _ = queryset.soft_delete()
        self.message_user(
            request,
            f'{deleted_count} lore record(s) soft-deleted.',
            messages.SUCCESS,
        )

    @admin.action(description='Restore selected soft-deleted lore records')
    def restore_selected(self, request, queryset):
        restored_count, _ = queryset.restore()
        self.message_user(
            request,
            f'{restored_count} lore record(s) restored.',
            messages.SUCCESS,
        )


@admin.register(LoreSource)
class LoreSourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'source_type', 'url', 'citation')
    list_filter = ('source_type',)
    search_fields = ('title', 'url', 'citation', 'notes')
