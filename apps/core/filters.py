import django_filters
from django import forms
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter


class SortOrderingFilter(OrderingFilter):
    """Support the documented ``sort``/``order`` pair and legacy ``ordering``."""

    sort_param = 'sort'
    order_param = 'order'
    order_values = ('asc', 'desc')

    def get_ordering(self, request, queryset, view):
        params = request.query_params
        if self.sort_param not in params and self.order_param not in params:
            return super().get_ordering(request, queryset, view)

        sort_values = params.getlist(self.sort_param)
        order_values = params.getlist(self.order_param)
        if len(sort_values) > 1 or len(order_values) > 1:
            raise ValidationError({'sort': 'Specify one sort field and one order direction.'})

        sort = sort_values[0].strip() if sort_values else ''
        order = order_values[0] if order_values else 'asc'
        if not sort:
            raise ValidationError({'sort': 'A sort field is required when using order.'})
        if order not in self.order_values:
            raise ValidationError({'order': 'Choose either "asc" or "desc".'})

        valid_fields = [
            field_name
            for field_name, _ in self.get_valid_fields(queryset, view, {'request': request})
        ]
        if sort not in valid_fields:
            raise ValidationError(
                {
                    'sort': (
                        f'"{sort}" is not a valid sort field. '
                        f'Choose from: {", ".join(valid_fields)}.'
                    )
                }
            )

        return [sort if order == 'asc' else f'-{sort}']


class StrictBooleanWidget(forms.Widget):
    """Keep raw query values so the field can reject noncanonical forms."""

    def value_from_datadict(self, data, files, name):
        values = data.getlist(name) if hasattr(data, 'getlist') else [data.get(name)]
        if not values:
            return None
        if len(values) > 1:
            return values
        return values[0]


class StrictBooleanField(forms.Field):
    """Accept only lowercase ``true`` and ``false`` query values."""

    def to_python(self, value):
        if value is None:
            return None
        if value == 'true':
            return True
        if value == 'false':
            return False
        raise DjangoValidationError('Enter either "true" or "false".', code='invalid')


class StrictBooleanFilter(django_filters.BooleanFilter):
    """Boolean query filter that rejects aliases and malformed values."""

    field_class = StrictBooleanField

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', StrictBooleanWidget())
        super().__init__(*args, **kwargs)


class StrictChoiceFilter(django_filters.ChoiceFilter):
    """Reject invalid choice query parameters instead of returning no results."""

    def filter(self, qs, value):
        if value and value not in dict(self.field.choices):
            valid_choices = ', '.join(dict(self.field.choices))
            raise ValidationError(
                {
                    'error': {
                        'code': 'BAD_REQUEST',
                        'message': (
                            f"'{value}' is not a valid choice for this filter. "
                            f'Valid options are: {valid_choices}'
                        ),
                    }
                }
            )
        return super().filter(qs, value)
