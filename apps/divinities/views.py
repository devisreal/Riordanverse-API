from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from apps.divinities.filters import GodFilter, TitanFilter
from apps.divinities.models import God, GodImage, Titan, TitanImage
from apps.divinities.serializers import (
    GodDetailSerializer,
    GodListSerializer,
    TitanDetailSerializer,
    TitanListSerializer,
)
from apps.images.filters import ImageFilter
from apps.images.models import Image
from apps.images.serializers import ImageSerializer


class GodListView(generics.ListAPIView):
    """GET /api/v1/gods/"""

    queryset = (
        God.objects.prefetch_related(
            'images__image',
            'books_appeared_in',
            'children_demigods',
            'weapons',
        )
        .select_related('first_appearance_book')
        .all()
    )
    serializer_class = GodListSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = GodFilter
    ordering_fields = ('name', 'tier', 'cabin_number')
    ordering = ('name',)


class GodDetailView(generics.RetrieveAPIView):
    """GET /api/v1/gods/<slug>/"""

    queryset = (
        God.objects.prefetch_related(
            'images__image',
            'books_appeared_in',
            'children_demigods',
            'weapons',
            'relationships_as_from__to_god',
            'relationships_as_from__to_titan',
            'relationships_as_to__from_god',
            'relationships_as_to__from_titan',
        )
        .select_related('first_appearance_book')
        .all()
    )
    serializer_class = GodDetailSerializer
    lookup_field = 'slug'


class _EntityImageListView(generics.ListAPIView):
    serializer_class = ImageSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ImageFilter
    entity_slug_kwarg = 'slug'

    def get_queryset(self):
        self.get_entity()
        links = self.get_links_queryset()
        gallery_order = Subquery(links.filter(image_id=OuterRef('pk')).values('display_order')[:1])
        return (
            Image.objects.filter(pk__in=links.values('image_id'))
            .annotate(_gallery_order=gallery_order)
            .order_by('_gallery_order', 'pk')
        )

    def get_entity(self):
        raise NotImplementedError

    def get_links_queryset(self):
        raise NotImplementedError


class GodImageListView(_EntityImageListView):
    """GET /api/v1/gods/<slug>/images/"""

    def get_entity(self):
        return get_object_or_404(God, slug=self.kwargs[self.entity_slug_kwarg])

    def get_links_queryset(self):
        self.get_entity()
        return GodImage.objects.filter(god__slug=self.kwargs[self.entity_slug_kwarg])


class TitanListView(generics.ListAPIView):
    """GET /api/v1/titans/"""

    queryset = (
        Titan.objects.prefetch_related('images__image', 'books_appeared_in')
        .select_related('first_appearance_book')
        .all()
    )
    serializer_class = TitanListSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = TitanFilter
    ordering_fields = ('name', 'alignment', 'status')
    ordering = ('name',)


class TitanDetailView(generics.RetrieveAPIView):
    """GET /api/v1/titans/<slug>/"""

    queryset = (
        Titan.objects.prefetch_related(
            'images__image',
            'books_appeared_in',
            'relationships_as_from__to_god',
            'relationships_as_from__to_titan',
            'relationships_as_to__from_god',
            'relationships_as_to__from_titan',
        )
        .select_related('first_appearance_book')
        .all()
    )
    serializer_class = TitanDetailSerializer
    lookup_field = 'slug'


class TitanImageListView(_EntityImageListView):
    """GET /api/v1/titans/<slug>/images/"""

    def get_entity(self):
        return get_object_or_404(Titan, slug=self.kwargs[self.entity_slug_kwarg])

    def get_links_queryset(self):
        self.get_entity()
        return TitanImage.objects.filter(titan__slug=self.kwargs[self.entity_slug_kwarg])
