import json
import tempfile
from io import BytesIO, StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase

from apps.images.wiki_image_audit import (
    FandomImageAuditClient,
    WikiImageAuditError,
    is_allowlisted_license,
)


class WikiImageLicenseTests(SimpleTestCase):
    def test_allowlists_explicit_permissive_licenses(self):
        for license_url in (
            'https://creativecommons.org/licenses/by/4.0/',
            'https://creativecommons.org/licenses/by-sa/3.0/',
            'https://creativecommons.org/publicdomain/zero/1.0/',
        ):
            with self.subTest(license_url=license_url):
                self.assertTrue(is_allowlisted_license(license_url))

    def test_rejects_noncommercial_unknown_and_non_creative_commons_licenses(self):
        for license_url in (
            'https://creativecommons.org/licenses/by-nc-sa/4.0/',
            'https://creativecommons.org/licenses/by-nd/4.0/',
            'https://example.com/license',
            'http://creativecommons.org/licenses/by/4.0/',
            None,
            '',
        ):
            with self.subTest(license_url=license_url):
                self.assertFalse(is_allowlisted_license(license_url))

    @patch('apps.images.wiki_image_audit.urlopen')
    def test_scan_page_returns_only_allowlisted_images_and_placeholder_signal(self, mock_urlopen):
        page_response = {
            'query': {
                'pages': [
                    {
                        'title': 'Percy Jackson',
                        'images': [
                            {'title': 'File:Licensed.jpg'},
                            {'title': 'File:Unclear.png'},
                        ],
                    }
                ]
            }
        }
        info_response = {
            'query': {
                'pages': [
                    {
                        'title': 'File:Licensed.jpg',
                        'imageinfo': [
                            {
                                'url': 'https://static.example/licensed.jpg',
                                'thumburl': 'https://static.example/thumb.jpg',
                                'width': 1200,
                                'height': 800,
                                'mime': 'image/jpeg',
                                'extmetadata': {
                                    'LicenseShortName': {'value': 'CC BY 4.0'},
                                    'LicenseUrl': {
                                        'value': 'https://creativecommons.org/licenses/by/4.0/'
                                    },
                                    'Artist': {
                                        'value': '<a href="/wiki/User:Artist">Artist Name</a>'
                                    },
                                },
                            }
                        ],
                    },
                    {
                        'title': 'File:Unclear.png',
                        'imageinfo': [
                            {
                                'url': 'https://static.example/unclear.png',
                                'extmetadata': {},
                            }
                        ],
                    },
                ]
            }
        }
        mock_urlopen.side_effect = [
            BytesIO(json.dumps(page_response).encode()),
            BytesIO(json.dumps(info_response).encode()),
        ]

        audit = FandomImageAuditClient(request_delay=0).scan_page(
            'https://riordan.fandom.com/wiki/Percy_Jackson'
        )

        self.assertFalse(audit['use_placeholder'])
        self.assertEqual(len(audit['images']), 1)
        self.assertEqual(audit['images'][0]['url'], 'https://static.example/licensed.jpg')
        self.assertEqual(audit['images'][0]['artist_name'], 'Artist Name')
        self.assertEqual(
            audit['images'][0]['artist_url'],
            'https://riordan.fandom.com/wiki/User:Artist',
        )
        self.assertEqual(audit['images'][0]['license_status'], 'allowlisted_candidate')
        self.assertEqual(
            audit['excluded_images'][0]['reason'],
            'license is missing or not on the reuse allowlist',
        )
        self.assertNotIn('url', audit['excluded_images'][0])

    @patch('apps.images.wiki_image_audit.urlopen')
    def test_include_all_images_keeps_urls_but_does_not_record_license(self, mock_urlopen):
        page_response = {
            'query': {'pages': [{'title': 'Page', 'images': [{'title': 'File:Unknown.png'}]}]}
        }
        info_response = {
            'query': {
                'pages': [
                    {
                        'title': 'File:Unknown.png',
                        'imageinfo': [
                            {
                                'url': 'https://static.example/unknown.png',
                                'width': 640,
                                'height': 480,
                                'mime': 'image/png',
                                'extmetadata': {},
                            }
                        ],
                    }
                ]
            }
        }
        mock_urlopen.side_effect = [
            BytesIO(json.dumps(page_response).encode()),
            BytesIO(json.dumps(info_response).encode()),
        ]

        audit = FandomImageAuditClient(request_delay=0).scan_page(
            'https://riordan.fandom.com/wiki/Page', include_all_images=True
        )

        self.assertFalse(audit['use_placeholder'])
        self.assertEqual(len(audit['images']), 1)
        image = audit['images'][0]
        self.assertEqual(image['url'], 'https://static.example/unknown.png')
        self.assertEqual(image['alt_text'], 'Unknown')
        self.assertEqual(image['file_format'], 'png')
        self.assertIsNone(image['license'])
        self.assertIsNone(image['license_url'])
        self.assertEqual(image['license_status'], 'not_recorded')

    def test_image_titles_follow_mediawiki_continuation_tokens(self):
        client = FandomImageAuditClient(request_delay=0)
        with patch.object(
            client,
            '_request',
            side_effect=[
                {
                    'query': {'pages': [{'images': [{'title': 'File:First.jpg'}]}]},
                    'continue': {'imcontinue': 'next', 'continue': '-||'},
                },
                {'query': {'pages': [{'images': [{'title': 'File:Second.jpg'}]}]}},
            ],
        ) as mock_request:
            titles = client._image_titles('https://riordan.fandom.com/api.php', 'Page')

        self.assertEqual(titles, ['File:First.jpg', 'File:Second.jpg'])
        self.assertEqual(mock_request.call_count, 2)

    def test_rejects_wiki_urls_outside_the_riordan_fandom_domain(self):
        with self.assertRaisesRegex(WikiImageAuditError, 'Unsupported wiki host'):
            FandomImageAuditClient().scan_page('https://example.com/wiki/Page')

    def test_no_allowlisted_images_requests_placeholder(self):
        with (
            patch.object(FandomImageAuditClient, '_image_titles', return_value=[]),
            patch.object(FandomImageAuditClient, '_image_info', return_value={}),
        ):
            audit = FandomImageAuditClient().scan_page('https://riordan.fandom.com/wiki/Unknown')

        self.assertTrue(audit['use_placeholder'])
        self.assertEqual(audit['images'], [])


class AuditWikiImagesCommandTests(SimpleTestCase):
    @patch('apps.images.management.commands.audit_wiki_images.FandomImageAuditClient')
    def test_command_writes_page_report_without_database_import(self, client_class):
        client_class.return_value.scan_page.return_value = {
            'source_page_url': 'https://riordan.fandom.com/wiki/Percy_Jackson',
            'images': [],
            'excluded_images': [{'file_title': 'File:Unknown.jpg', 'reason': 'no license'}],
            'use_placeholder': True,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            seed_path = Path(temp_dir) / 'characters.json'
            report_path = Path(temp_dir) / 'audit.json'
            seed_path.write_text(
                json.dumps(
                    [
                        {
                            'name': 'Percy Jackson',
                            'expected_slug': 'percy-jackson',
                            'wiki_url': 'https://riordan.fandom.com/wiki/Percy_Jackson',
                        }
                    ]
                )
            )
            stdout = StringIO()

            call_command(
                'audit_wiki_images',
                '--input',
                str(seed_path),
                '--output',
                str(report_path),
                stdout=stdout,
            )

            report = json.loads(report_path.read_text())

        self.assertFalse(report['license_policy']['database_changes'])
        self.assertEqual(report['entities'][0]['entity_slug'], 'percy-jackson')
        self.assertTrue(report['entities'][0]['use_placeholder'])
        self.assertIn('1 placeholder fallback', stdout.getvalue())

    @patch('apps.images.management.commands.audit_wiki_images.FandomImageAuditClient')
    def test_include_all_images_option_passes_through_and_records_policy(self, client_class):
        client_class.return_value.scan_page.return_value = {
            'source_page_url': 'https://riordan.fandom.com/wiki/Percy_Jackson',
            'images': [
                {
                    'url': 'https://static.example/percy.jpg',
                    'license': None,
                    'license_url': None,
                    'license_status': 'not_recorded',
                }
            ],
            'excluded_images': [],
            'use_placeholder': False,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            seed_path = Path(temp_dir) / 'characters.json'
            report_path = Path(temp_dir) / 'images.json'
            seed_path.write_text(
                json.dumps(
                    [
                        {
                            'name': 'Percy Jackson',
                            'expected_slug': 'percy-jackson',
                            'wiki_url': 'https://riordan.fandom.com/wiki/Percy_Jackson',
                        }
                    ]
                )
            )

            call_command(
                'audit_wiki_images',
                '--input',
                str(seed_path),
                '--output',
                str(report_path),
                '--include-all-images',
                stdout=StringIO(),
            )

            report = json.loads(report_path.read_text())

        client_class.return_value.scan_page.assert_called_once_with(
            'https://riordan.fandom.com/wiki/Percy_Jackson', include_all_images=True
        )
        self.assertTrue(report['license_policy']['include_all_images'])
        self.assertFalse(report['license_policy']['license_metadata_recorded'])
        self.assertIsNone(report['entities'][0]['images'][0]['license'])
