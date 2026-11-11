from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import yaml
from django.conf import settings
from django.test import SimpleTestCase

from website.content import LORE_CORRECTION_URL


class LoreCorrectionFormTests(SimpleTestCase):
    def test_link_resolves_to_one_structured_template_and_readme_uses_same_destination(self):
        query = parse_qs(urlsplit(LORE_CORRECTION_URL).query)
        self.assertEqual(query, {'template': ['lore_correction.yml']})
        directory = Path(settings.BASE_DIR) / '.github' / 'ISSUE_TEMPLATE'
        template = yaml.safe_load((directory / query['template'][0]).read_text())
        self.assertEqual(template['name'], 'Lore correction')
        self.assertFalse((directory / 'lore_correction.md').exists())
        readme = (Path(settings.BASE_DIR) / 'README.md').read_text()
        self.assertIn(f']({LORE_CORRECTION_URL})', readme)

    def test_form_requires_resource_current_information_correction_and_evidence(self):
        path = Path(settings.BASE_DIR) / '.github' / 'ISSUE_TEMPLATE' / 'lore_correction.yml'
        template = yaml.safe_load(path.read_text())
        fields = [field for field in template['body'] if 'id' in field]
        ids = [field['id'] for field in fields]
        self.assertEqual(len(ids), len(set(ids)))
        by_id = {field['id']: field for field in fields}
        for field_id in ('resource', 'current_information', 'suggested_correction', 'evidence'):
            with self.subTest(field=field_id):
                self.assertTrue(by_id[field_id]['validations']['required'])
                self.assertTrue(by_id[field_id]['attributes']['label'])
        self.assertTrue(by_id['public_submission']['attributes']['options'][0]['required'])
        notice = template['body'][0]['attributes']['value']
        for reminder in ('public GitHub issue', 'reviewed manually', 'API keys', 'copyrighted'):
            self.assertIn(reminder, notice)
