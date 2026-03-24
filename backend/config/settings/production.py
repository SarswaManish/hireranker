import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *

DEBUG = False

# Security
# Render terminates TLS at the load balancer and forwards via HTTP internally.
# SECURE_PROXY_SSL_HEADER tells Django to trust X-Forwarded-Proto: https.
# SECURE_SSL_REDIRECT is OFF because the redirect would loop on Render/Vercel.
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CORS — explicit origins + regex for Vercel preview deployments
CORS_ALLOWED_ORIGINS = [o for o in config('CORS_ALLOWED_ORIGINS', default='', cast=Csv()) if o]
CORS_ALLOWED_ORIGIN_REGEXES = [r for r in config('CORS_ALLOWED_ORIGIN_REGEXES', default='', cast=Csv()) if r]

# ── File Storage ──────────────────────────────────────────────────────────────
# Set USE_S3=true + AWS_* vars to enable S3.
# On Render free tier, leave USE_S3=false — files are stored locally but will
# NOT persist across deploys (acceptable for MVP / demo use).
USE_S3 = config('USE_S3', default='false', cast=lambda v: v.lower() == 'true')

if USE_S3:
    AWS_S3_CUSTOM_DOMAIN = config(
        'AWS_S3_CUSTOM_DOMAIN',
        default=f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com',
    )
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    AWS_LOCATION = 'media'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_ROOT = BASE_DIR / 'media'
    MEDIA_URL = '/media/'

# Static files via whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── Redis / Celery ─────────────────────────────────────────────────────────────
# Upstash Redis URLs start with rediss:// (TLS).
# Django cache uses CONNECTION_POOL_KWARGS; Celery requires ssl_cert_reqs in the URL itself.
_redis_url = REDIS_URL  # already set from base via decouple
if _redis_url.startswith('rediss://'):
    _ssl_opts = {'ssl_cert_reqs': None}
    CACHES['default']['OPTIONS']['CONNECTION_POOL_KWARGS'].update(_ssl_opts)

    # Append ssl_cert_reqs=CERT_NONE to Celery broker/backend URLs so the
    # redis.py backend does not raise ValueError on startup.
    def _add_ssl_param(url: str) -> str:
        sep = '&' if '?' in url else '?'
        return url if 'ssl_cert_reqs' in url else f'{url}{sep}ssl_cert_reqs=CERT_NONE'

    CELERY_BROKER_URL = _add_ssl_param(CELERY_BROKER_URL)
    CELERY_RESULT_BACKEND = _add_ssl_param(CELERY_RESULT_BACKEND)

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@hireranker.com')

# Celery
CELERY_TASK_ALWAYS_EAGER = False

# Sentry
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(transaction_style='url', middleware_spans=True),
            CeleryIntegration(monitor_beat_tasks=True),
            RedisIntegration(),
        ],
        traces_sample_rate=config('SENTRY_TRACES_SAMPLE_RATE', default=0.1, cast=float),
        profiles_sample_rate=config('SENTRY_PROFILES_SAMPLE_RATE', default=0.1, cast=float),
        send_default_pii=False,
        environment='production',
        release=config('APP_VERSION', default='1.0.0'),
    )

# Logging — console only on Render (no writable log dir on free tier)
LOGGING['root']['level'] = 'WARNING'
LOGGING['loggers']['apps']['handlers'] = ['console']
LOGGING['loggers']['tasks']['handlers'] = ['console']
