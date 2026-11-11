from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from apps.core.filters import SortOrderingFilter
from apps.images.filters import ImageFilter
from apps.images.models import Image
from apps.images.serializers import ImageSerializer


class ImageListView(generics.ListAPIView):
    """GET /api/v1/images/"""

    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = ImageFilter
    ordering_fields = ('id', 'url', 'source_type', 'category', 'uploaded_at')
    ordering = ('id',)
