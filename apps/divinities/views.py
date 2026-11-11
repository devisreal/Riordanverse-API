from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from apps.core.filters import SortOrderingFilter
from apps.divinities.family import prefetch_family
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

    queryset = God.objects.prefetch_related(
        'images__image',
        'books_appeared_in',
        'weapons',
    ).select_related('first_appearance_book')
    serializer_class = GodListSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = GodFilter
    ordering_fields = ('name', 'tier', 'cabin_number')
    ordering = ('name',)


class GodDetailView(generics.RetrieveAPIView):
    """GET /api/v1/gods/<slug>/"""

    queryset = prefetch_family(
        God.objects.prefetch_related(
            'images__image',
            'books_appeared_in',
            'weapons',
        )
        .select_related('first_appearance_book')
        .all()
    )
    serializer_class = GodDetailSerializer
    lookup_field = 'slug'


class _EntityImageListView(generics.ListAPIView):
    serializer_class = ImageSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = ImageFilter
    entity_slug_kwarg = 'slug'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Image.objects.none()
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

    queryset = Titan.objects.prefetch_related('images__image', 'books_appeared_in').select_related(
        'first_appearance_book'
    )
    serializer_class = TitanListSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = TitanFilter
    ordering_fields = ('display_order', 'name', 'alignment', 'status')


class TitanDetailView(generics.RetrieveAPIView):
    """GET /api/v1/titans/<slug>/"""

    queryset = prefetch_family(
        Titan.objects.prefetch_related('images__image', 'books_appeared_in', 'weapons')
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


class GodChildrenListView(generics.ListAPIView):
    """GET /api/v1/gods/<slug>/children/"""

    def get_queryset(self):
        from apps.characters.models import Character
        from apps.divinities.models import God

        if getattr(self, 'swagger_fake_view', False):
            return Character.objects.none()
        get_object_or_404(God, slug=self.kwargs['slug'])
        return Character.objects.filter(
            divine_relationships_as_to__from_god__slug=self.kwargs['slug'],
            divine_relationships_as_to__relationship_type='parent_of',
        ).distinct()

    def get_serializer_class(self):
        from apps.characters.serializers import CharacterListSerializer

        return CharacterListSerializer


class GodWeaponListView(generics.ListAPIView):
    """GET /api/v1/gods/<slug>/weapons/"""

    def get_queryset(self):
        from apps.divinities.models import God
        from apps.items.models import Weapon

        if getattr(self, 'swagger_fake_view', False):
            return Weapon.objects.none()
        get_object_or_404(God, slug=self.kwargs['slug'])
        return Weapon.objects.filter(associated_gods__slug=self.kwargs['slug']).distinct()

    def get_serializer_class(self):
        from apps.items.serializers import WeaponListSerializer

        return WeaponListSerializer
