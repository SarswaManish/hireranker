from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Development-specific installed apps
INSTALLED_APPS += []

# Local file storage (default Django behavior)
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery - do not use eager in development so background tasks work properly
# Set CELERY_TASK_ALWAYS_EAGER=True only for unit tests
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=False, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = config('CELERY_TASK_ALWAYS_EAGER', default=False, cast=bool)

# Development database - can use SQLite by setting USE_SQLITE=True
# USE_SQLITE = config('USE_SQLITE', default=False, cast=bool)
# if USE_SQLITE:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': BASE_DIR / 'db.sqlite3',
#         }
#     }

# Django Debug Toolbar (install separately if needed)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
# INTERNAL_IPS = ['127.0.0.1']

# Looser password validation in development
AUTH_PASSWORD_VALIDATORS = []

# CORS - allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Disable HTTPS redirect in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Logging more verbose in development
LOGGING['loggers']['apps']['level'] = 'DEBUG'
LOGGING['loggers']['tasks']['level'] = 'DEBUG'
LOGGING['loggers']['core']['level'] = 'DEBUG'
LOGGING['root']['level'] = 'DEBUG'
