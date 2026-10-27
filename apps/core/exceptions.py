from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class InvalidFilterValue(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'INVALID_FILTER_VALUE'

    def __init__(self, parameter: str, value: str, valid_values: list[str]):
        self.error_payload = {
            'code': self.default_code,
            'message': f"{parameter}: '{value}' is not a valid choice.",
            'valid_values': list(valid_values),
        }
        super().__init__(detail=self.error_payload['message'], code=self.default_code)


def custom_exception_handler(exc, context):
    """Wrap handled DRF errors in the documented error response envelope."""
    response = exception_handler(exc, context)
    if response is None:
        # Let Django handle unhandled exceptions as server errors.
        return None

    if isinstance(exc, InvalidFilterValue):
        response.data = {'error': exc.error_payload}
        return response

    response.data = {
        'error': {
            'code': _get_code(response.status_code),
            'message': _get_message(response.data),
        }
    }
    return response


def _get_code(status_code: int) -> str:
    mapping = {
        status.HTTP_400_BAD_REQUEST: 'BAD_REQUEST',
        status.HTTP_401_UNAUTHORIZED: 'UNAUTHORIZED',
        status.HTTP_403_FORBIDDEN: 'FORBIDDEN',
        status.HTTP_404_NOT_FOUND: 'NOT_FOUND',
        status.HTTP_405_METHOD_NOT_ALLOWED: 'METHOD_NOT_ALLOWED',
        status.HTTP_429_TOO_MANY_REQUESTS: 'RATE_LIMITED',
        status.HTTP_500_INTERNAL_SERVER_ERROR: 'INTERNAL_SERVER_ERROR',
    }
    return mapping.get(status_code, 'ERROR')


def _get_message(data) -> str:
    """Flatten DRF's string, list, or field-error dictionary to readable text."""
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        return ' '.join(str(item) for item in data)
    if isinstance(data, dict):
        parts = []
        for key, value in data.items():
            if key == 'detail':
                parts.append(str(value))
            elif isinstance(value, list):
                parts.append(f'{key}: {", ".join(str(item) for item in value)}')
            else:
                parts.append(f'{key}: {value}')
        return ' | '.join(parts)
    return str(data)
