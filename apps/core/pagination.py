from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class EnvelopePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response(
            {
                'data': data,
                'meta': {
                    'total': self.page.paginator.count,
                    'page': self.page.number,
                    'limit': self.get_page_size(self.request),
                    'total_pages': self.page.paginator.num_pages,
                },
            }
        )

    def get_paginated_response_schema(self, schema):
        """Provide the response envelope schema to drf-spectacular."""
        return {
            'type': 'object',
            'properties': {
                'data': schema,
                'meta': {
                    'type': 'object',
                    'properties': {
                        'total': {'type': 'integer'},
                        'page': {'type': 'integer'},
                        'limit': {'type': 'integer'},
                        'total_pages': {'type': 'integer'},
                    },
                },
            },
        }
