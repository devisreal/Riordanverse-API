from drf_spectacular.extensions import OpenApiFilterExtension, OpenApiSerializerFieldExtension
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import build_parameter_type

from apps.core.permissions import CachedHasAPIKey


class APIKeyAutoSchema(AutoSchema):
    """Document the API-key permission without exposing DRF session/basic auth."""

    def get_auth(self):
        permissions = self.view.get_permissions()
        if any(isinstance(permission, CachedHasAPIKey) for permission in permissions):
            return [{'ApiKeyAuth': []}]
        return super().get_auth()

    def get_tags(self):
        return [tag.replace('_', ' ').title() for tag in super().get_tags()]


_REFERENCE_SCHEMA = {
    'type': 'object',
    'required': ['name', 'type', 'slug'],
    'properties': {
        'name': {'type': 'string'},
        'type': {'type': 'string'},
        'slug': {'type': 'string'},
    },
}


class SortOrderingFilterSchemaExtension(OpenApiFilterExtension):
    """Expose the actual sort/order aliases alongside legacy `ordering`."""

    target_class = 'apps.core.filters.SortOrderingFilter'
    priority = 1

    def get_schema_operation_parameters(self, auto_schema, *args, **kwargs):
        view = auto_schema.view
        queryset = view.get_queryset()
        valid_fields = [
            field_name
            for field_name, _ in self.target.get_valid_fields(
                queryset,
                view,
                {'request': view.request},
            )
        ]
        return [
            build_parameter_type(
                name='sort',
                schema={'type': 'string'},
                location='query',
                enum=valid_fields,
                description='One allowlisted field; required when `order` is supplied.',
            ),
            build_parameter_type(
                name='order',
                schema={'type': 'string'},
                location='query',
                enum=['asc', 'desc'],
                default='asc',
                description='Direction for `sort`; only lowercase `asc` or `desc` is accepted.',
            ),
            build_parameter_type(
                name='ordering',
                schema={'type': 'string'},
                location='query',
                description=(
                    'Legacy DRF ordering parameter. Use comma-separated allowlisted fields; '
                    'prefix a field with `-` for descending order.'
                ),
            ),
        ]


class SerializerMethodFieldSchemaExtension(OpenApiSerializerFieldExtension):
    """Give computed response fields explicit, shared OpenAPI types."""

    target_class = 'rest_framework.serializers.SerializerMethodField'
    priority = 1

    def map_serializer_field(self, auto_schema, direction):
        name = self.target.field_name
        if name == 'family':
            return {
                'type': 'object',
                'required': ['parents', 'siblings', 'consorts', 'children'],
                'properties': {
                    relation: {
                        'type': 'array',
                        'items': _REFERENCE_SCHEMA,
                    }
                    for relation in ('parents', 'siblings', 'consorts', 'children')
                },
            }
        if name == 'narrators':
            return {'type': 'array', 'items': _REFERENCE_SCHEMA}
        if name in {'controlled_by', 'owner_primary', 'forged_by', 'leader'}:
            return {**_REFERENCE_SCHEMA, 'nullable': True}
        if name.endswith('_slugs') or name in {'participant_slugs', 'casualty_slugs'}:
            return {'type': 'array', 'items': {'type': 'string'}}
        if name.endswith('_slug') or name == 'slug':
            return {'type': 'string', 'nullable': True}
        if name.endswith('_count'):
            return {'type': 'integer'}
        if name == 'primary_image':
            return {'type': 'string', 'format': 'uri', 'nullable': True}
        if name == 'url':
            return {'type': 'string', 'format': 'uri-reference', 'nullable': True}
        if name == 'prophecy_lines':
            return {'type': 'array', 'items': {'type': 'string'}}
        if name == 'material_display':
            return {'type': 'string'}
        return {'type': 'string'}
