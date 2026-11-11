from urllib.parse import urlencode

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse

from apps.bestiary.models import Monster, MonsterImage
from apps.characters.models import Character, CharacterImage
from apps.divinities.models import God, GodImage, Titan, TitanImage
from apps.images.models import Image
from apps.items.models import Weapon, WeaponImage
from apps.locations.models import Location, LocationImage
from apps.narrative.models import Book, BookImage

GALLERY_TYPES = (
    {
        'key': 'books',
        'label': 'Books',
        'entity_model': Book,
        'link_model': BookImage,
        'entity_fk': 'book',
        'label_field': 'title',
    },
    {
        'key': 'characters',
        'label': 'Characters',
        'entity_model': Character,
        'link_model': CharacterImage,
        'entity_fk': 'character',
        'label_field': 'name',
    },
    {
        'key': 'gods',
        'label': 'Gods',
        'entity_model': God,
        'link_model': GodImage,
        'entity_fk': 'god',
        'label_field': 'name',
    },
    {
        'key': 'titans',
        'label': 'Titans',
        'entity_model': Titan,
        'link_model': TitanImage,
        'entity_fk': 'titan',
        'label_field': 'name',
    },
    {
        'key': 'monsters',
        'label': 'Monsters',
        'entity_model': Monster,
        'link_model': MonsterImage,
        'entity_fk': 'monster',
        'label_field': 'name',
    },
    {
        'key': 'weapons',
        'label': 'Weapons',
        'entity_model': Weapon,
        'link_model': WeaponImage,
        'entity_fk': 'weapon',
        'label_field': 'name',
    },
    {
        'key': 'locations',
        'label': 'Locations',
        'entity_model': Location,
        'link_model': LocationImage,
        'entity_fk': 'location',
        'label_field': 'name',
    },
)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    change_list_template = 'admin/images/image/change_list.html'
    list_display = (
        'id',
        'source_type',
        'category',
        'artist_name',
        'license',
        'license_url',
        'uploaded_at',
    )
    list_filter = ('source_type', 'category')
    search_fields = ('alt_text', 'artist_name', 'license', 'license_url', 'url')
    readonly_fields = ('uploaded_at',)

    def changelist_view(self, request, extra_context=None):
        context = {
            **(extra_context or {}),
            'can_use_primary_picker': self.has_change_permission(request),
        }
        return super().changelist_view(request, extra_context=context)

    def get_urls(self):
        custom_urls = [
            path(
                'primary-picker/',
                self.admin_site.admin_view(self.primary_picker_view),
                name='images_image_primary_picker',
            )
        ]
        return custom_urls + super().get_urls()

    def primary_picker_view(self, request):
        if not self.has_change_permission(request):
            raise PermissionDenied

        entity_key = (
            request.POST.get('entity', '')
            if request.method == 'POST'
            else request.GET.get('entity', '')
        )
        gallery_config, entity = self._resolve_entity(entity_key)
        picker_url = reverse('admin:images_image_primary_picker')

        if request.method == 'POST':
            if not gallery_config or not entity:
                messages.error(request, 'Select a valid entity before saving a primary image.')
                return redirect(picker_url)
            if not request.user.has_perm(
                f'{gallery_config["link_model"]._meta.app_label}.'
                f'change_{gallery_config["link_model"]._meta.model_name}'
            ):
                raise PermissionDenied

            raw_primary_link_id = request.POST.get('primary_link_id', '')
            try:
                primary_link_id = int(raw_primary_link_id) if raw_primary_link_id else None
            except TypeError, ValueError:
                messages.error(request, 'Select a valid image from this gallery.')
                return redirect(f'{picker_url}?{urlencode({"entity": entity_key})}')

            links = gallery_config['link_model'].objects.filter(
                **{gallery_config['entity_fk']: entity}
            )
            if primary_link_id is not None and not links.filter(pk=primary_link_id).exists():
                messages.error(request, 'That image is not part of the selected entity gallery.')
                return redirect(f'{picker_url}?{urlencode({"entity": entity_key})}')

            with transaction.atomic():
                gallery_config['entity_model'].objects.select_for_update().get(pk=entity.pk)
                links.update(is_primary=False)
                if primary_link_id is not None:
                    links.filter(pk=primary_link_id).update(is_primary=True)

            if primary_link_id is not None:
                messages.success(request, 'Primary image saved for this gallery.')
            else:
                messages.success(request, 'Primary image cleared for this gallery.')
            return redirect(f'{picker_url}?{urlencode({"entity": entity_key})}')

        links = []
        current_primary_id = None
        selected_entity_label = None
        gallery_groups = self._gallery_groups()
        if gallery_config and entity:
            links = list(
                gallery_config['link_model']
                .objects.filter(**{gallery_config['entity_fk']: entity})
                .select_related('image')
                .order_by('display_order', 'pk')
            )
            current_primary = next((link for link in links if link.is_primary), None)
            current_primary_id = current_primary.pk if current_primary else None
            selected_entity_label = (
                f'{gallery_config["label"]}: {getattr(entity, gallery_config["label_field"])}'
            )
        elif entity_key:
            messages.error(request, 'That entity is not available in the image galleries.')
            entity_key = ''

        context = {
            **self.admin_site.each_context(request),
            'title': 'Choose a primary image',
            'opts': self.model._meta,
            'gallery_groups': gallery_groups,
            'selected_entity_key': entity_key,
            'selected_entity_label': selected_entity_label,
            'links': links,
            'current_primary_id': current_primary_id,
            'picker_url': picker_url,
        }
        return TemplateResponse(request, 'admin/images/image/primary_picker.html', context)

    @staticmethod
    def _resolve_entity(entity_key):
        if not entity_key:
            return None, None
        try:
            key, raw_pk = entity_key.split(':', 1)
            config = next(config for config in GALLERY_TYPES if config['key'] == key)
            entity = config['entity_model'].objects.filter(pk=int(raw_pk)).first()
        except StopIteration, TypeError, ValueError:
            return None, None
        return (config, entity) if entity else (None, None)

    @staticmethod
    def _gallery_groups():
        groups = []
        for config in GALLERY_TYPES:
            counts = {
                row[config['entity_fk']]: row['image_count']
                for row in config['link_model']
                .objects.values(config['entity_fk'])
                .annotate(image_count=Count('pk'))
            }
            entities = (
                config['entity_model'].objects.filter(pk__in=counts).order_by(config['label_field'])
            )
            options = [
                {
                    'value': f'{config["key"]}:{entity.pk}',
                    'label': f'{getattr(entity, config["label_field"])} ({counts[entity.pk]})',
                }
                for entity in entities
            ]
            if options:
                groups.append({'label': config['label'], 'options': options})
        return groups
