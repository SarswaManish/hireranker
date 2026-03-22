from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Nested under /api/projects/{project_pk}/
urlpatterns = [
    path(
        'projects/<uuid:project_pk>/import/',
        views.CandidateImportBatchViewSet.as_view({
            'post': 'create',
            'get': 'list',
        }),
        name='candidate-import-list',
    ),
    path(
        'projects/<uuid:project_pk>/import/<uuid:pk>/',
        views.CandidateImportBatchViewSet.as_view({
            'get': 'retrieve',
        }),
        name='candidate-import-detail',
    ),
    path(
        'projects/<uuid:project_pk>/candidates/',
        views.CandidateViewSet.as_view({
            'get': 'list',
        }),
        name='candidate-list',
    ),
    path(
        'projects/<uuid:project_pk>/candidates/column_suggestions/',
        views.CandidateViewSet.as_view({
            'get': 'column_suggestions',
            'post': 'column_suggestions',
        }),
        name='candidate-column-suggestions',
    ),
    path(
        'projects/<uuid:project_pk>/candidates/<uuid:pk>/',
        views.CandidateViewSet.as_view({
            'get': 'retrieve',
            'patch': 'partial_update',
        }),
        name='candidate-detail',
    ),
    path(
        'projects/<uuid:project_pk>/candidates/<uuid:pk>/add_tag/',
        views.CandidateViewSet.as_view({
            'post': 'add_tag',
        }),
        name='candidate-add-tag',
    ),
    path(
        'projects/<uuid:project_pk>/candidates/<uuid:pk>/tags/<uuid:tag_id>/',
        views.CandidateViewSet.as_view({
            'delete': 'remove_tag',
        }),
        name='candidate-remove-tag',
    ),
    path(
        'projects/<uuid:project_pk>/query/',
        views.RecruiterQueryView.as_view(),
        name='recruiter-query',
    ),
]
