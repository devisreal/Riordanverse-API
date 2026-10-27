from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from apps.core.filters import SortOrderingFilter
from apps.images.filters import ImageFilter
from apps.images.models import Image
from apps.images.serializers import ImageSerializer
from apps.items.filters import WeaponFilter
from apps.items.models import Weapon, WeaponImage
from apps.items.serializers import WeaponDetailSerializer, WeaponListSerializer


class WeaponListView(generics.ListAPIView):
    """GET /api/v1/weapons/"""

    queryset = (
        Weapon.objects.prefetch_related('images__image', 'books_appeared_in')
        .select_related(
            'owner_primary_character',
            'owner_primary_god',
            'owner_primary_titan',
            'forged_by',
            'forged_by_character',
            'first_appearance_book',
        )
        .all()
    )
    serializer_class = WeaponListSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = WeaponFilter
    ordering_fields = ('name', 'weapon_type', 'material')
    ordering = ('name',)


class WeaponDetailView(generics.RetrieveAPIView):
    """GET /api/v1/weapons/<slug>/"""

    queryset = (
        Weapon.objects.prefetch_related('images__image', 'books_appeared_in')
        .select_related(
            'owner_primary_character',
            'owner_primary_god',
            'owner_primary_titan',
            'forged_by',
            'forged_by_character',
            'first_appearance_book',
        )
        .all()
    )
    serializer_class = WeaponDetailSerializer
    lookup_field = 'slug'


class WeaponImageListView(generics.ListAPIView):
    """GET /api/v1/weapons/<slug>/images/"""

    serializer_class = ImageSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = ImageFilter

    def get_queryset(self):
        get_object_or_404(Weapon, slug=self.kwargs['slug'])
        links = WeaponImage.objects.filter(weapon__slug=self.kwargs['slug'])
        gallery_order = Subquery(links.filter(image_id=OuterRef('pk')).values('display_order')[:1])
        return (
            Image.objects.filter(pk__in=links.values('image_id'))
            .annotate(_gallery_order=gallery_order)
            .order_by('_gallery_order', 'pk')
        )
