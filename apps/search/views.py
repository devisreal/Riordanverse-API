import watson.search as watson
from django.apps import apps as django_apps
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import InvalidFilterValue
from apps.search.serializers import MODEL_TYPE_MAP, SearchResultSerializer

# Derive supported filters from the serializer's canonical model map.
TYPE_TO_MODEL = {type_label: model_key for model_key, (type_label, _) in MODEL_TYPE_MAP.items()}
VALID_TYPES = tuple(sorted(TYPE_TO_MODEL))


def _get_model_class(type_label):
    """Resolve a public type label to its registered Django model."""
    model_key = TYPE_TO_MODEL[type_label]
    app_label, model_name = model_key.split('.')
    return django_apps.get_model(app_label, model_name)


class SearchView(APIView):
    """Search all indexed lore models, optionally restricted by ``type``."""

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        type_filter = request.query_params.get('type', '').strip()

        if not query:
            raise ValidationError("Query parameter 'q' is required and cannot be blank.")

        if type_filter and type_filter not in TYPE_TO_MODEL:
            raise InvalidFilterValue('type', type_filter, VALID_TYPES)

        if type_filter:
            results = watson.search(query, models=(_get_model_class(type_filter),))
        else:
            results = watson.search(query)

        serialized_results = SearchResultSerializer(results, many=True).data
        return Response(
            {
                'data': serialized_results,
                'meta': {
                    'total': len(serialized_results),
                    'query': query,
                    'type_filter': type_filter or None,
                },
            }
        )
