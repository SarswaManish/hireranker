from django.urls import path

from . import views

urlpatterns = [
    path(
        'projects/<uuid:project_pk>/rankings/',
        views.ProjectRankingsView.as_view(),
        name='project-rankings',
    ),
    path(
        'projects/<uuid:project_pk>/evaluate/',
        views.TriggerEvaluationView.as_view(),
        name='trigger-evaluation',
    ),
    path(
        'projects/<uuid:project_pk>/evaluate/status/',
        views.TriggerEvaluationView.as_view(),
        name='evaluation-status',
    ),
    path(
        'projects/<uuid:project_pk>/candidates/<uuid:candidate_pk>/evaluation/',
        views.CandidateEvaluationDetailView.as_view(),
        name='candidate-evaluation',
    ),
    path(
        'projects/<uuid:project_pk>/compare/',
        views.CompareCandidatesView.as_view(),
        name='compare-candidates',
    ),
]
