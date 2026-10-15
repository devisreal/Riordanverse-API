import django_filters
from rest_framework.exceptions import ValidationError


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
