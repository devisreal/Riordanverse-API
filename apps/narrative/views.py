from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from apps.images.filters import ImageFilter
from apps.images.models import Image
from apps.images.serializers import ImageSerializer
from apps.narrative.filters import BookFilter
from apps.narrative.models import Book, BookImage
from apps.narrative.serializers import BookDetailSerializer, BookListSerializer


class BookListView(generics.ListAPIView):
    """GET /api/v1/books/"""

    queryset = (
        Book.objects.prefetch_related('images__image', 'main_characters', 'antagonists')
        .select_related('narrator')
        .all()
    )
    serializer_class = BookListSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = BookFilter
    ordering_fields = ('book_number', 'published_date', 'title')
    ordering = ('series', 'book_number')


class BookDetailView(generics.RetrieveAPIView):
    """GET /api/v1/books/<slug>/"""

    queryset = (
        Book.objects.prefetch_related('images__image', 'main_characters', 'antagonists')
        .select_related('narrator')
        .all()
    )
    serializer_class = BookDetailSerializer
    lookup_field = 'slug'


class BookImageListView(generics.ListAPIView):
    """GET /api/v1/books/<slug>/images/"""

    serializer_class = ImageSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ImageFilter

    def get_queryset(self):
        get_object_or_404(Book, slug=self.kwargs['slug'])
        book_images = BookImage.objects.filter(book__slug=self.kwargs['slug'])
        gallery_order = Subquery(
            book_images.filter(image_id=OuterRef('pk')).values('display_order')[:1]
        )
        return (
            Image.objects.filter(pk__in=book_images.values('image_id'))
            .annotate(_gallery_order=gallery_order)
            .order_by('_gallery_order', 'pk')
        )
