from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from apps.bestiary.filters import CreatureFilter, MonsterFilter
from apps.bestiary.models import Creature, Monster, MonsterImage
from apps.bestiary.serializers import (
    CreatureDetailSerializer,
    CreatureListSerializer,
    MonsterDetailSerializer,
    MonsterListSerializer,
)
from apps.core.filters import SortOrderingFilter
from apps.divinities.family import prefetch_family
from apps.images.filters import ImageFilter
from apps.images.models import Image
from apps.images.serializers import ImageSerializer


class MonsterListView(generics.ListAPIView):
    """GET /api/v1/monsters/"""

    queryset = Monster.objects.prefetch_related(
        'images__image',
        'defeated_by',
        'defeated_by_gods',
        'defeats__defeated_by',
        'defeats__book',
        'books_appeared_in',
    ).select_related('first_appearance_book')
    serializer_class = MonsterListSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = MonsterFilter
    ordering_fields = ('name', 'allegiance', 'monster_type')
    ordering = ('name',)


class MonsterDetailView(generics.RetrieveAPIView):
    """GET /api/v1/monsters/<slug>/"""

    queryset = prefetch_family(
        Monster.objects.prefetch_related(
            'images__image',
            'defeated_by',
            'defeated_by_gods',
            'defeats__defeated_by',
            'defeats__book',
            'books_appeared_in',
        )
        .select_related('first_appearance_book')
        .all()
    )
    serializer_class = MonsterDetailSerializer
    lookup_field = 'slug'


class MonsterImageListView(generics.ListAPIView):
    """GET /api/v1/monsters/<slug>/images/"""

    serializer_class = ImageSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = ImageFilter

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Image.objects.none()
        get_object_or_404(Monster, slug=self.kwargs['slug'])
        links = MonsterImage.objects.filter(monster__slug=self.kwargs['slug'])
        gallery_order = Subquery(links.filter(image_id=OuterRef('pk')).values('display_order')[:1])
        return (
            Image.objects.filter(pk__in=links.values('image_id'))
            .annotate(_gallery_order=gallery_order)
            .order_by('_gallery_order', 'pk')
        )


class CreatureListView(generics.ListAPIView):
    """GET /api/v1/creatures/"""

    queryset = Creature.objects.prefetch_related('notable_members').all()
    serializer_class = CreatureListSerializer
    filter_backends = (DjangoFilterBackend, SortOrderingFilter)
    filterset_class = CreatureFilter
    ordering_fields = ('name', 'alignment')
    ordering = ('name',)


class CreatureDetailView(generics.RetrieveAPIView):
    """GET /api/v1/creatures/<slug>/"""

    queryset = prefetch_family(
        Creature.objects.prefetch_related(
            'member_records__member_character',
            'member_records__member_monster',
            'notable_members',
        ).all()
    )
    serializer_class = CreatureDetailSerializer
    lookup_field = 'slug'


class CreatureMemberListView(generics.ListAPIView):
    """GET /api/v1/creatures/<slug>/members/"""

    def get_queryset(self):
        from apps.bestiary.models import Creature
        from apps.characters.models import Character

        if getattr(self, 'swagger_fake_view', False):
            return Character.objects.none()
        get_object_or_404(Creature, slug=self.kwargs['slug'])
        return Character.objects.filter(creature_species__slug=self.kwargs['slug']).distinct()

    def get_serializer_class(self):
        from apps.characters.serializers import CharacterListSerializer

        return CharacterListSerializer
