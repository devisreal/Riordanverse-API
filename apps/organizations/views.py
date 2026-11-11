from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from apps.core.filters import SortOrderingFilter
from apps.organizations.filters import CabinFilter, FactionFilter
from apps.organizations.models import Cabin, Faction, FactionMember
from apps.organizations.serializers import (
    CabinDetailSerializer,
    CabinListSerializer,
    FactionDetailSerializer,
    FactionListSerializer,
    FactionMemberSerializer,
)


class CabinListView(generics.ListAPIView):
    """GET /api/v1/cabins/"""

    queryset = (
        Cabin.objects.prefetch_related('known_campers')
        .select_related('deity', 'head_counselor', 'added_in_book')
        .all()
    )
    serializer_class = CabinListSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
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
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = FactionFilter
    ordering_fields = ('name', 'alignment')
    ordering = ('name',)


class FactionDetailView(generics.RetrieveAPIView):
    """GET /api/v1/factions/<slug>/"""

    queryset = (
        Faction.objects.prefetch_related(
            'members',
            'member_records__member_character',
            'member_records__member_god',
            'member_records__member_titan',
            'member_records__member_monster',
            'books_active_in',
        )
        .select_related('leader_character', 'leader_god')
        .all()
    )
    serializer_class = FactionDetailSerializer
    lookup_field = 'slug'


class CabinCamperListView(generics.ListAPIView):
    """GET /api/v1/cabins/<slug>/campers/"""

    def get_queryset(self):
        from apps.characters.models import Character
        from apps.organizations.models import Cabin

        if getattr(self, 'swagger_fake_view', False):
            return Character.objects.none()
        get_object_or_404(Cabin, slug=self.kwargs['slug'])
        return Character.objects.filter(cabin__slug=self.kwargs['slug']).distinct()

    def get_serializer_class(self):
        from apps.characters.serializers import CharacterListSerializer

        return CharacterListSerializer


class FactionMemberListView(generics.ListAPIView):
    """GET /api/v1/factions/<slug>/members/"""

    serializer_class = FactionMemberSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return FactionMember.objects.none()
        get_object_or_404(Faction, slug=self.kwargs['slug'])
        return FactionMember.objects.filter(faction__slug=self.kwargs['slug']).select_related(
            'member_character', 'member_god', 'member_titan', 'member_monster'
        )
