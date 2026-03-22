import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    USER_REGISTERED = 'USER_REGISTERED'
    PROJECT_CREATED = 'PROJECT_CREATED'
    FILE_UPLOADED = 'FILE_UPLOADED'
    CANDIDATES_IMPORTED = 'CANDIDATES_IMPORTED'
    EVALUATION_STARTED = 'EVALUATION_STARTED'
    EVALUATION_COMPLETED = 'EVALUATION_COMPLETED'
    EXPORT_DOWNLOADED = 'EXPORT_DOWNLOADED'
    QUERY_ASKED = 'QUERY_ASKED'
    USER_LOGIN = 'USER_LOGIN'
    USER_LOGOUT = 'USER_LOGOUT'
    ORG_CREATED = 'ORG_CREATED'
    ORG_MEMBER_INVITED = 'ORG_MEMBER_INVITED'
    PAYMENT_COMPLETED = 'PAYMENT_COMPLETED'


def log_event(user, event_type: AuditEventType, metadata: dict = None) -> None:
    """
    Create an audit log entry.

    Args:
        user: User instance (can be None for system events)
        event_type: AuditEventType enum value
        metadata: Additional data dict
    """
    from apps.core.models import AuditLog

    if metadata is None:
        metadata = {}

    # Convert any non-serializable values
    clean_metadata = {}
    for k, v in metadata.items():
        if hasattr(v, '__str__'):
            clean_metadata[str(k)] = str(v) if not isinstance(v, (int, float, bool, list, dict, type(None))) else v
        else:
            clean_metadata[str(k)] = str(v)

    try:
        AuditLog.objects.create(
            user=user,
            event_type=str(event_type),
            metadata=clean_metadata,
        )
    except Exception as e:
        # Never let audit logging crash the main flow
        logger.error("Failed to create audit log: %s", e)


def check_database_health() -> str:
    """Check if the database is accessible."""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return 'ok'
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        return 'error'


def check_redis_health() -> str:
    """Check if Redis is accessible."""
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', timeout=5)
        value = cache.get('health_check')
        if value == 'ok':
            return 'ok'
        return 'error'
    except Exception as e:
        logger.error("Redis health check failed: %s", e)
        return 'error'


def get_client_ip(request) -> Optional[str]:
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def truncate_text(text: str, max_length: int, suffix: str = '...') -> str:
    """Truncate text to max_length, adding suffix if truncated."""
    if not text:
        return ''
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def chunks(lst: list, n: int):
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
