from django.urls import path

from . import views

urlpatterns = [
    path(
        'projects/<uuid:project_pk>/export/csv/',
        views.ExportRankingsCSVView.as_view(),
        name='export-rankings-csv',
    ),
    path(
        'projects/<uuid:project_pk>/export/candidates/csv/',
        views.ExportCandidatesCSVView.as_view(),
        name='export-candidates-csv',
    ),
]
