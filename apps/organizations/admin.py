from django.contrib import admin

from apps.organizations.models import Cabin, Faction, FactionMember


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


class FactionMemberInline(admin.TabularInline):
    model = FactionMember
    extra = 0
    raw_id_fields = ('member_character', 'member_god', 'member_titan', 'member_monster')


@admin.register(Faction)
class FactionAdmin(admin.ModelAdmin):
    list_display = ('name', 'faction_type', 'alignment')
    list_filter = ('faction_type', 'alignment')
    search_fields = ('name', 'description')
    raw_id_fields = ('leader_character', 'leader_god')
    filter_horizontal = ('books_active_in',)
    inlines = (FactionMemberInline,)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FactionMember)
class FactionMemberAdmin(admin.ModelAdmin):
    list_display = ('faction', 'member_type', 'member_display')
    list_filter = ('faction__faction_type',)
    search_fields = (
        'faction__name',
        'member_character__name',
        'member_god__name',
        'member_titan__name',
        'member_monster__name',
    )
    raw_id_fields = ('faction', 'member_character', 'member_god', 'member_titan', 'member_monster')

    @admin.display(description='Entity type')
    def member_type(self, obj):
        for member_type in ('character', 'god', 'titan', 'monster'):
            if getattr(obj, f'member_{member_type}_id'):
                return member_type
        return '—'

    @admin.display(description='Member')
    def member_display(self, obj):
        return obj.member_character or obj.member_god or obj.member_titan or obj.member_monster
