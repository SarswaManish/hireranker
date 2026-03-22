import logging

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied as DRFPermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class HireRankerAPIException(APIException):
    """Base exception for HireRanker API."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'An unexpected error occurred.'
    default_code = 'server_error'


class ResourceNotFoundError(HireRankerAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'The requested resource was not found.'
    default_code = 'not_found'


class AccessDeniedError(HireRankerAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'access_denied'


class InvalidOperationError(HireRankerAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'This operation is not valid in the current state.'
    default_code = 'invalid_operation'


class ExternalServiceError(HireRankerAPIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'An external service is unavailable.'
    default_code = 'service_unavailable'


class LLMServiceError(ExternalServiceError):
    default_detail = 'The AI evaluation service is currently unavailable.'
    default_code = 'llm_unavailable'


class PaymentError(HireRankerAPIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = 'Payment required or failed.'
    default_code = 'payment_error'


def custom_exception_handler(exc, context):
    """
    Custom exception handler that wraps all errors in consistent format:
    {"data": null, "message": "...", "errors": {...}}
    """
    # Call DRF's default handler first
    response = exception_handler(exc, context)

    if response is not None:
        # DRF handled the exception
        original_data = response.data
        message = _extract_message(exc, original_data)
        errors = _extract_errors(original_data)

        response.data = {
            'data': None,
            'message': message,
            'errors': errors,
        }
        return response

    # Handle Django exceptions
    if isinstance(exc, Http404):
        return Response(
            {'data': None, 'message': 'Not found', 'errors': None},
            status=status.HTTP_404_NOT_FOUND
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            {'data': None, 'message': 'Permission denied', 'errors': None},
            status=status.HTTP_403_FORBIDDEN
        )

    if isinstance(exc, DjangoValidationError):
        return Response(
            {'data': None, 'message': 'Validation error', 'errors': {'detail': exc.messages}},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Unhandled exception - log it
    logger.error("Unhandled exception in view: %s", exc, exc_info=True)
    return Response(
        {'data': None, 'message': 'An unexpected error occurred', 'errors': None},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def _extract_message(exc, data) -> str:
    """Extract a human-readable message from exception."""
    if isinstance(exc, NotAuthenticated):
        return 'Authentication required'
    if isinstance(exc, AuthenticationFailed):
        return 'Authentication failed'
    if isinstance(exc, DRFPermissionDenied):
        return str(exc.detail) if hasattr(exc, 'detail') else 'Permission denied'
    if isinstance(exc, NotFound):
        return 'Not found'
    if isinstance(exc, ValidationError):
        return 'Validation failed'
    if hasattr(exc, 'default_detail'):
        return str(exc.default_detail)
    if isinstance(data, dict) and 'detail' in data:
        return str(data['detail'])
    return 'An error occurred'


def _extract_errors(data) -> dict | None:
    """Extract errors dict from response data."""
    if isinstance(data, dict):
        if 'detail' in data and len(data) == 1:
            return None  # Simple detail message
        # Remove 'detail' from errors if present
        errors = {k: v for k, v in data.items() if k != 'detail'}
        return errors if errors else None
    if isinstance(data, list):
        return {'detail': data}
    return None
