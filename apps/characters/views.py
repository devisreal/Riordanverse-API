from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from apps.characters.filters import CharacterFilter
from apps.characters.models import Character, CharacterImage
from apps.characters.serializers import CharacterDetailSerializer, CharacterListSerializer
from apps.images.filters import ImageFilter
from apps.images.models import Image
from apps.images.serializers import ImageSerializer


class CharacterListView(generics.ListAPIView):
    """GET /api/v1/characters/"""

    queryset = (
        Character.objects.prefetch_related(
            'images__image',
            'books_appeared_in',
            'siblings',
            'weapons',
            'powers',
        )
        .select_related(
            'divine_parent',
            'divine_parent_titan',
            'mortal_parent_ref',
            'empathy_link',
            'first_appearance_book',
        )
        .all()
    )
    serializer_class = CharacterListSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = CharacterFilter
    ordering_fields = ('name', 'status', 'age_first_appearance')
    ordering = ('name',)


class CharacterDetailView(generics.RetrieveAPIView):
    """GET /api/v1/characters/<slug>/"""

    queryset = (
        Character.objects.prefetch_related(
            'images__image',
            'books_appeared_in',
            'siblings',
            'weapons',
            'powers',
        )
        .select_related(
            'divine_parent',
            'divine_parent_titan',
            'mortal_parent_ref',
            'empathy_link',
            'first_appearance_book',
        )
        .all()
    )
    serializer_class = CharacterDetailSerializer
    lookup_field = 'slug'


class CharacterImageListView(generics.ListAPIView):
    """GET /api/v1/characters/<slug>/images/"""

    serializer_class = ImageSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ImageFilter

    def get_queryset(self):
        get_object_or_404(Character, slug=self.kwargs['slug'])
        links = CharacterImage.objects.filter(character__slug=self.kwargs['slug'])
        gallery_order = Subquery(links.filter(image_id=OuterRef('pk')).values('display_order')[:1])
        return (
            Image.objects.filter(pk__in=links.values('image_id'))
            .annotate(_gallery_order=gallery_order)
            .order_by('_gallery_order', 'pk')
        )


class CharacterWeaponListView(generics.ListAPIView):
    """GET /api/v1/characters/<slug>/weapons/"""

    def get_queryset(self):
        from apps.items.models import Weapon

        get_object_or_404(Character, slug=self.kwargs['slug'])
        return Weapon.objects.filter(wielded_by__slug=self.kwargs['slug']).distinct()

    def get_serializer_class(self):
        from apps.items.serializers import WeaponListSerializer

        return WeaponListSerializer


class CharacterQuestListView(generics.ListAPIView):
    """GET /api/v1/characters/<slug>/quests/"""

    def get_queryset(self):
        from apps.narrative.models import Quest

        get_object_or_404(Character, slug=self.kwargs['slug'])
        return (
            Quest.objects.filter(participants__slug=self.kwargs['slug'])
            .select_related('book', 'led_by')
            .distinct()
        )

    def get_serializer_class(self):
        from apps.narrative.serializers import QuestListSerializer

        return QuestListSerializer
