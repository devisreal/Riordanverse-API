import django_filters

from apps.core.choices import IMAGE_CATEGORY_CHOICES, IMAGE_SOURCE_TYPE_CHOICES
from apps.core.filters import StrictChoiceFilter
from apps.images.models import Image


class ImageFilter(django_filters.FilterSet):
    """Shared source/category and exact provenance filters for image collections."""

    source_type = StrictChoiceFilter(choices=IMAGE_SOURCE_TYPE_CHOICES)
    category = StrictChoiceFilter(choices=IMAGE_CATEGORY_CHOICES)
    source_url = django_filters.CharFilter(field_name='source_url', lookup_expr='exact')
    wiki_url = django_filters.CharFilter(field_name='wiki_url', lookup_expr='exact')

    class Meta:
        model = Image
        fields = ('source_type', 'category', 'source_url', 'wiki_url')
