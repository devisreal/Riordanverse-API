from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from apps.core.filters import SortOrderingFilter
from apps.images.filters import ImageFilter
from apps.images.models import Image
from apps.images.serializers import ImageSerializer
from apps.locations.filters import LocationFilter
from apps.locations.models import Location, LocationImage
from apps.locations.serializers import LocationDetailSerializer, LocationListSerializer


class LocationListView(generics.ListAPIView):
    """GET /api/v1/locations/"""

    queryset = (
        Location.objects.prefetch_related('images__image', 'books_appeared_in')
        .select_related(
            'controlled_by_god',
            'controlled_by_titan',
            'controlled_by_character',
            'controlled_by_monster',
            'first_appearance_book',
            'earlier_mention_book',
        )
        .all()
    )
    serializer_class = LocationListSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = LocationFilter
    ordering_fields = ('location_order', 'name', 'location_type')


class LocationDetailView(generics.RetrieveAPIView):
    """GET /api/v1/locations/<slug>/"""

    queryset = (
        Location.objects.prefetch_related('images__image', 'books_appeared_in')
        .select_related(
            'controlled_by_god',
            'controlled_by_titan',
            'controlled_by_character',
            'controlled_by_monster',
            'first_appearance_book',
            'earlier_mention_book',
        )
        .all()
    )
    serializer_class = LocationDetailSerializer
    lookup_field = 'slug'


class LocationImageListView(generics.ListAPIView):
    """GET /api/v1/locations/<slug>/images/"""

    serializer_class = ImageSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = ImageFilter

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Image.objects.none()
        get_object_or_404(Location, slug=self.kwargs['slug'])
        links = LocationImage.objects.filter(location__slug=self.kwargs['slug'])
        gallery_order = Subquery(links.filter(image_id=OuterRef('pk')).values('display_order')[:1])
        return (
            Image.objects.filter(pk__in=links.values('image_id'))
            .annotate(_gallery_order=gallery_order)
            .order_by('_gallery_order', 'pk')
        )
