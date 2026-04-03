from uuid import uuid4

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    code = 'error'
    detail = 'Request failed.'
    fields = {}

    if isinstance(exc, ValidationError):
        code = 'validation_error'
        detail = 'Validation failed.'
        if isinstance(response.data, dict):
            fields = response.data
    elif response.status_code == status.HTTP_401_UNAUTHORIZED:
        code = 'unauthorized'
        detail = 'Authentication required or invalid token.'
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        code = 'forbidden'
        detail = 'You do not have permission to perform this action.'
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        code = 'not_found'
        detail = 'Resource not found.'

    response.data = {
        'code': code,
        'detail': detail,
        'fields': fields,
        'trace_id': str(uuid4()),
    }
    return response
