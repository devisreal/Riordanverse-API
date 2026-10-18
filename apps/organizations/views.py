from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from apps.organizations.filters import CabinFilter, FactionFilter
from apps.organizations.models import Cabin, Faction
from apps.organizations.serializers import (
    CabinDetailSerializer,
    CabinListSerializer,
    FactionDetailSerializer,
    FactionListSerializer,
)


class CabinListView(generics.ListAPIView):
    """GET /api/v1/cabins/"""

    queryset = (
        Cabin.objects.prefetch_related('known_campers')
        .select_related('deity', 'head_counselor', 'added_in_book')
        .all()
    )
    serializer_class = CabinListSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = CabinFilter
    ordering_fields = ('number',)
    ordering = ('number',)


class CabinDetailView(generics.RetrieveAPIView):
    """GET /api/v1/cabins/<slug>/"""

    queryset = (
        Cabin.objects.prefetch_related('known_campers')
        .select_related('deity', 'head_counselor', 'added_in_book')
        .all()
    )
    serializer_class = CabinDetailSerializer
    lookup_field = 'slug'


class CabinByNumberView(generics.RetrieveAPIView):
    """GET /api/v1/cabins/number/<number>/"""

    queryset = (
        Cabin.objects.prefetch_related('known_campers')
        .select_related('deity', 'head_counselor', 'added_in_book')
        .all()
    )
    serializer_class = CabinDetailSerializer
    lookup_field = 'number'
    lookup_url_kwarg = 'number'


class FactionListView(generics.ListAPIView):
    """GET /api/v1/factions/"""

    queryset = (
        Faction.objects.prefetch_related('members', 'books_active_in')
        .select_related('leader_character', 'leader_god')
        .all()
    )
    serializer_class = FactionListSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = FactionFilter
    ordering_fields = ('name', 'alignment')
    ordering = ('name',)


class FactionDetailView(generics.RetrieveAPIView):
    """GET /api/v1/factions/<slug>/"""

    queryset = (
        Faction.objects.prefetch_related('members', 'books_active_in')
        .select_related('leader_character', 'leader_god')
        .all()
    )
    serializer_class = FactionDetailSerializer
    lookup_field = 'slug'
