import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.images.wiki_image_audit import FandomImageAuditClient, WikiImageAuditError


class Command(BaseCommand):
    help = (
        'Audit images on wiki pages listed in seed JSON and write a read-only '
        'report of explicitly licensed candidates and placeholder fallbacks.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--input',
            action='append',
            required=True,
            help='Seed JSON file; may be supplied multiple times.',
        )
        parser.add_argument(
            '--output',
            required=True,
            help='Path to write the JSON audit report.',
        )
        parser.add_argument(
            '--user-agent',
            default=None,
            help='Optional User-Agent value for MediaWiki API requests.',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=20,
            help='HTTP timeout in seconds (default: 20).',
        )
        parser.add_argument(
            '--request-delay',
            type=float,
            default=0.25,
            help='Minimum delay between API requests in seconds (default: 0.25).',
        )
        parser.add_argument(
            '--include-all-images',
            action='store_true',
            help='Include all image URLs and leave license fields blank.',
        )

    def handle(self, *args, **options):
        input_paths = [Path(path) for path in options['input']]
        missing_paths = [str(path) for path in input_paths if not path.is_file()]
        if missing_paths:
            raise CommandError(f'Input file(s) not found: {", ".join(missing_paths)}')

        client_options = {
            'timeout': options['timeout'],
            'request_delay': options['request_delay'],
        }
        if options['user_agent']:
            client_options['user_agent'] = options['user_agent']
        client = FandomImageAuditClient(**client_options)

        report = {
            'license_policy': {
                'allowlist': [
                    'Creative Commons Attribution (CC BY)',
                    'Creative Commons Attribution-ShareAlike (CC BY-SA)',
                    'CC0 1.0 Universal',
                ],
                'excluded_images': (
                    'Unclear or non-allowlisted licenses are excluded.'
                    if not options['include_all_images']
                    else 'No images are excluded; reuse permission is not asserted.'
                ),
                'include_all_images': options['include_all_images'],
                'license_metadata_recorded': False,
                'database_changes': False,
            },
            'input_files': [str(path) for path in input_paths],
            'entities': [],
        }

        for input_path in input_paths:
            try:
                records = json.loads(input_path.read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise CommandError(f'Could not read {input_path}: {exc}') from exc
            if not isinstance(records, list):
                raise CommandError(f'{input_path} must contain a JSON list.')

            for record in records:
                if not isinstance(record, dict):
                    continue
                page_url = record.get('wiki_url')
                if not page_url:
                    continue

                entity = {
                    'entity_type': input_path.stem,
                    'entity_slug': record.get('expected_slug') or record.get('slug'),
                    'entity_name': (
                        record.get('name') or record.get('title') or record.get('true_name')
                    ),
                }
                try:
                    if not isinstance(page_url, str):
                        raise WikiImageAuditError('wiki_url must be a string.')
                    audit = client.scan_page(
                        page_url,
                        include_all_images=options['include_all_images'],
                    )
                except WikiImageAuditError as exc:  # Keep other pages in the batch usable.
                    audit = {
                        'source_page_url': page_url,
                        'images': [],
                        'excluded_images': [],
                        'use_placeholder': True,
                        'scan_error': str(exc),
                    }
                    self.stderr.write(self.style.WARNING(f'Could not audit {page_url}: {exc}'))
                report['entities'].append({**entity, **audit})

        output_path = Path(options['output'])
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
        except OSError as exc:
            raise CommandError(f'Could not write {output_path}: {exc}') from exc

        scanned = len(report['entities'])
        approved = sum(len(entity['images']) for entity in report['entities'])
        placeholders = sum(entity['use_placeholder'] for entity in report['entities'])
        image_label = (
            'image URL(s) included with no license recorded'
            if options['include_all_images']
            else 'allowlisted image candidate(s)'
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Audited {scanned} wiki page(s): {approved} {image_label}, '
                f'{placeholders} placeholder fallback(s). Report: {output_path}'
            )
        )
