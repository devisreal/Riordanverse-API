"""Seed URL-backed image metadata and supported entity gallery links."""

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError, transaction

from apps.bestiary.models import Monster, MonsterImage
from apps.characters.models import Character, CharacterImage
from apps.divinities.models import God, GodImage, Titan, TitanImage
from apps.images.models import Image
from apps.images.seed_matching import should_link_image
from apps.items.models import Weapon, WeaponImage
from apps.locations.models import Location, LocationImage
from apps.narrative.models import Book, BookImage

DATA_FILE = settings.BASE_DIR / 'data' / 'images.json'
GALLERY_OVERRIDES_FILE = settings.BASE_DIR / 'data' / 'image_gallery_overrides.json'

SUPPORTED_IMAGE_LINKS = {
    'books': (Book, BookImage, 'book'),
    'characters': (Character, CharacterImage, 'character'),
    'gods': (God, GodImage, 'god'),
    'titans': (Titan, TitanImage, 'titan'),
    'monsters': (Monster, MonsterImage, 'monster'),
    'weapons': (Weapon, WeaponImage, 'weapon'),
    'locations': (Location, LocationImage, 'location'),
}


class Command(BaseCommand):
    help = 'Seed wiki image URLs and supported entity gallery links from data/images.json.'

    def handle(self, *args, **options):
        if not DATA_FILE.exists():
            self.stderr.write(self.style.ERROR(f'Data file not found: {DATA_FILE}'))
            return

        with DATA_FILE.open(encoding='utf-8') as data_file:
            payload = json.load(data_file)
        if GALLERY_OVERRIDES_FILE.exists():
            with GALLERY_OVERRIDES_FILE.open(encoding='utf-8') as overrides_file:
                gallery_overrides = json.load(overrides_file)
        else:
            gallery_overrides = {}

        entities = payload.get('entities', [])
        created_count = 0
        updated_count = 0
        linked_count = 0
        unresolved_count = 0
        error_count = 0

        for entity_record in entities:
            entity_type = entity_record.get('entity_type')
            entity_slug = entity_record.get('entity_slug')
            entity_name = (
                entity_record.get('entity_name')
                or entity_record.get('name')
                or entity_slug
                or 'unknown entity'
            )
            source_page_url = entity_record.get('source_page_url')
            supported = SUPPORTED_IMAGE_LINKS.get(entity_type)
            linked_entity = None
            image_link_model = supported[1] if supported else None
            image_link_foreign_key = supported[2] if supported else None
            linked_image_ids = set()
            entity_has_errors = False
            entity_overrides = gallery_overrides.get(entity_type, {}).get(entity_slug, {})
            include_file_titles = set(entity_overrides.get('include_file_titles', []))

            if supported and entity_slug:
                entity_model, _, _ = supported
                linked_entity = entity_model.objects.filter(slug=entity_slug).first()
                if linked_entity is None:
                    unresolved_count += 1
                    self.stderr.write(
                        self.style.WARNING(
                            f"[WARN] Unresolved {entity_type} '{entity_slug}' for "
                            f'{entity_name}; images will remain in the global collection.'
                        )
                    )
            elif supported:
                unresolved_count += 1
                self.stderr.write(
                    self.style.WARNING(
                        f'[WARN] Missing slug for {entity_type} {entity_name}; '
                        'images will remain in the global collection.'
                    )
                )

            for display_order, entry in enumerate(entity_record.get('images', [])):
                image_name = entry.get('file_title', entry.get('alt_text', 'unknown image'))
                url = entry.get('url')
                source_url = entry.get('source_url') or source_page_url
                if not url or not source_url:
                    error_count += 1
                    entity_has_errors = True
                    self.stderr.write(
                        self.style.ERROR(
                            f'  Skipped {image_name} for {entity_name}: missing image or source URL.'
                        )
                    )
                    continue

                matched_entity_image = linked_entity is not None and should_link_image(
                    entity_type,
                    entity_name,
                    entity_slug,
                    entry,
                    include_file_titles=include_file_titles,
                )
                defaults = {
                    'thumbnail_url': entry.get('thumbnail_url'),
                    'alt_text': (entry.get('alt_text') or image_name)[:255],
                    'source_type': 'wiki',
                    'category': (
                        'book_cover' if entity_type == 'books' and matched_entity_image else 'other'
                    ),
                    'artist_name': entry.get('artist_name'),
                    'artist_url': entry.get('artist_url'),
                    'source_url': source_url,
                    'license': None,
                    'license_url': None,
                    'width': entry.get('width'),
                    'height': entry.get('height'),
                    'file_format': (entry.get('file_format') or '')[:10] or None,
                    'wiki_url': entry.get('wiki_url'),
                }

                try:
                    with transaction.atomic():
                        image, created = Image.objects.update_or_create(
                            url=url,
                            source_url=source_url,
                            defaults=defaults,
                        )
                        if matched_entity_image:
                            image_link_model.objects.update_or_create(
                                image=image,
                                **{image_link_foreign_key: linked_entity},
                                defaults={'display_order': display_order},
                            )
                            linked_image_ids.add(image.pk)
                except (DatabaseError, KeyError, TypeError, ValueError) as exc:
                    error_count += 1
                    entity_has_errors = True
                    self.stderr.write(
                        self.style.ERROR(f'  Failed {image_name} for {entity_name}: {exc}')
                    )
                    continue

                if created:
                    created_count += 1
                else:
                    updated_count += 1
                if matched_entity_image:
                    linked_count += 1

            if linked_entity is not None and supported and not entity_has_errors:
                image_link_model.objects.filter(
                    **{image_link_foreign_key: linked_entity},
                    image__source_type='wiki',
                ).exclude(image_id__in=linked_image_ids).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Images seeded: {created_count} created, {updated_count} updated, '
                f'{linked_count} gallery links, {unresolved_count} unresolved entities, '
                f'{error_count} errors.'
            )
        )
