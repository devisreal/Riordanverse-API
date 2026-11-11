"""Ensure checked-in primary selections survive fresh imports and reseeding."""

import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.images.management.commands import seed_images
from apps.images.models import Image
from tests.makers import (
    make_book,
    make_character,
    make_god,
    make_location,
    make_monster,
    make_titan,
    make_weapon,
)


class CuratedPrimarySeedTests(TestCase):
    def test_checked_in_primaries_are_restored_on_fresh_and_repeat_imports(self):
        overrides = json.loads(seed_images.GALLERY_OVERRIDES_FILE.read_text(encoding='utf-8'))
        payload = json.loads(seed_images.DATA_FILE.read_text(encoding='utf-8'))
        records = {
            (record['entity_type'], record['entity_slug']): record for record in payload['entities']
        }
        makers = {
            'books': make_book,
            'characters': make_character,
            'gods': make_god,
            'titans': make_titan,
            'monsters': make_monster,
            'weapons': make_weapon,
            'locations': make_location,
        }
        selected_records = []
        expected = []
        for entity_type, entity_overrides in overrides.items():
            for slug, options in entity_overrides.items():
                title = options.get('primary_file_title')
                if not title:
                    continue
                with self.subTest(entity_type=entity_type, slug=slug):
                    record = records[(entity_type, slug)]
                    matches = [entry for entry in record['images'] if entry['file_title'] == title]
                    self.assertEqual(
                        len(matches), 1, 'Primary must identify exactly one seed image'
                    )
                    entry = matches[0]
                    name = record.get('entity_name') or record.get('name') or slug
                    fields = {'title' if entity_type == 'books' else 'name': name}
                    if entity_type == 'books':
                        fields['book_number'] = len(expected) + 1
                    entity = makers[entity_type](slug=slug, **fields)
                    _, link_model, foreign_key = seed_images.SUPPORTED_IMAGE_LINKS[entity_type]
                    expected.append(
                        (
                            link_model,
                            foreign_key,
                            entity,
                            entry['url'],
                            entry.get('source_url') or record['source_page_url'],
                        )
                    )
                    selected_records.append(record)
        self.assertTrue(expected, 'The dataset must contain curated primary selections')

        with TemporaryDirectory() as directory:
            data_file = Path(directory) / 'images.json'
            data_file.write_text(json.dumps({'entities': selected_records}), encoding='utf-8')
            with patch.object(seed_images, 'DATA_FILE', data_file):
                for run in range(2):
                    stdout, stderr = StringIO(), StringIO()
                    call_command('seed_images', stdout=stdout, stderr=stderr)
                    self.assertEqual(stderr.getvalue(), '')
                    self.assertIn('0 errors.', stdout.getvalue())
                    for link_model, foreign_key, entity, url, source_url in expected:
                        with self.subTest(run=run, entity=entity.slug):
                            primaries = link_model.objects.filter(
                                **{foreign_key: entity}, is_primary=True
                            )
                            self.assertEqual(primaries.count(), 1)
                            self.assertEqual(primaries.get().image.url, url)
                            self.assertEqual(primaries.get().image.source_url, source_url)
                    if run == 0:
                        image_count = Image.objects.count()
                        # Simulate a different admin choice; reseeding must restore the dataset.
                        for link_model, foreign_key, entity, url, source_url in expected:
                            links = link_model.objects.filter(**{foreign_key: entity})
                            links.update(is_primary=False)
                            alternate = links.exclude(
                                image__url=url, image__source_url=source_url
                            ).first()
                            if alternate:
                                alternate.is_primary = True
                                alternate.save(update_fields=['is_primary'])
                    else:
                        self.assertEqual(Image.objects.count(), image_count)
