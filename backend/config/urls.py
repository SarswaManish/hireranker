from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.utils import check_database_health, check_redis_health


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    db_status = check_database_health()
    redis_status = check_redis_health()
    overall = 'ok' if db_status == 'ok' and redis_status == 'ok' else 'degraded'
    return Response({
        'status': overall,
        'database': db_status,
        'redis': redis_status,
    })


urlpatterns = [
    path('admin/', admin.site.urls),

    # Health check
    path('api/health/', health_check, name='health-check'),

    # API Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # App URLs
    path('api/auth/', include('apps.accounts.urls')),
    path('api/organizations/', include('apps.organizations.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/', include('apps.candidates.urls')),
    path('api/', include('apps.resumes.urls')),
    path('api/', include('apps.evaluations.urls')),
    path('api/', include('apps.exports.urls')),
    path('api/billing/', include('apps.billing.urls')),
    path('api/review/', include('apps.billing.review_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
