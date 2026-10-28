from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.views import APIView

from apps.core.permissions import CachedHasAPIKey


class SchemaEndpointTests(APITestCase):
    def test_openapi_schema_is_public_and_declares_api_key_security(self):
        with patch.object(APIView, 'permission_classes', [CachedHasAPIKey]):
            response = self.client.get(reverse('schema'), {'format': 'json'})

        self.assertEqual(response.status_code, 200)
        schema = response.json()
        tag_names = [tag['name'] for tag in schema['tags']]
        self.assertEqual(tag_names[:4], ['Authentication', 'Health', 'Books', 'Characters'])
        self.assertEqual(
            schema['paths']['/api/v1/characters/']['get']['tags'],
            ['Characters'],
        )
        self.assertEqual(
            schema['components']['securitySchemes']['ApiKeyAuth'],
            {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API-Key',
                'description': 'Consumer API key. Request one at POST /auth/request-key/.',
            },
        )
        self.assertEqual(
            schema['paths']['/api/v1/characters/']['get']['security'],
            [{'ApiKeyAuth': []}],
        )
        self.assertEqual(schema['paths']['/health/live/']['get'].get('security', []), [])
        self.assertEqual(schema['paths']['/health/ready/']['get'].get('security', []), [])
        self.assertEqual(schema['paths']['/auth/request-key/']['post'].get('security', []), [])
        self.assertEqual(
            schema['paths']['/auth/revoke-key/']['post']['security'],
            [{'ApiKeyAuth': []}],
        )
        revoke_operation = schema['paths']['/auth/revoke-key/']['post']
        self.assertIn('400', revoke_operation['responses'])
        self.assertNotIn('requestBody', revoke_operation)
        self.assertEqual(
            set(schema['components']['schemas']['KeyRevocationResponse']['properties']),
            {'revoked', 'message'},
        )

        character_list = schema['paths']['/api/v1/characters/']['get']
        parameters = {parameter['name']: parameter for parameter in character_list['parameters']}
        self.assertEqual(
            parameters['sort']['schema']['enum'], ['age_first_appearance', 'name', 'status']
        )
        self.assertEqual(parameters['order']['schema']['enum'], ['asc', 'desc'])
        self.assertNotIn('default', parameters['order']['schema'])
        self.assertIn('Defaults to `asc` when omitted.', parameters['order']['description'])
        self.assertEqual(parameters['is_demigod']['schema']['type'], 'boolean')
        self.assertIn('ordering', parameters)
        self.assertIn('type', parameters)

        book_parameters = schema['paths']['/api/v1/books/']['get']['parameters']
        book_order = next(
            parameter for parameter in book_parameters if parameter['name'] == 'order'
        )
        self.assertNotIn('default', book_order['schema'])

        character_family = schema['components']['schemas']['CharacterDetail']['properties'][
            'family'
        ]
        self.assertEqual(
            set(character_family['properties']),
            {'parents', 'siblings', 'consorts', 'children'},
        )
        book_detail = schema['components']['schemas']['BookDetail']['properties']
        self.assertIn('main_characters', book_detail)
        self.assertIn('narrators', book_detail)
        self.assertIn('antagonists', book_detail)
        book_gods = schema['paths']['/api/v1/books/{slug}/gods/']['get']
        self.assertEqual(book_gods['tags'], ['Books'])
        self.assertEqual(book_gods['security'], [{'ApiKeyAuth': []}])
        for typed_serializer in (
            'QuestParticipant',
            'QuestCasualty',
            'ProphecySubject',
            'FactionMember',
        ):
            self.assertIn(typed_serializer, schema['components']['schemas'])

        cast_schema = schema['components']['schemas']['BookCastMember']
        self.assertEqual(set(cast_schema['properties']), {'name', 'type', 'slug'})
        self.assertEqual(
            schema['components']['schemas']['SearchResult']['properties']['url']['format'],
            'uri-reference',
        )
        key_header = next(
            parameter
            for parameter in schema['paths']['/auth/verify-key/']['post']['parameters']
            if parameter['name'] == 'X-API-Key' and parameter['in'] == 'header'
        )
        self.assertFalse(key_header.get('required', False))
        self.assertEqual(key_header['schema']['type'], 'string')

    def test_swagger_and_redoc_pages_are_public(self):
        with patch.object(APIView, 'permission_classes', [CachedHasAPIKey]):
            swagger = self.client.get(reverse('swagger-ui'))
            redoc = self.client.get(reverse('redoc'))

        self.assertEqual(swagger.status_code, 200)
        self.assertEqual(redoc.status_code, 200)
        self.assertIn(b'SwaggerUIBundle', swagger.content)
        self.assertIn(b'tagsSorter": null', swagger.content)
        self.assertIn(b'<redoc', redoc.content.lower())
