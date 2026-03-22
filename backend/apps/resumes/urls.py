from django.urls import path

from . import views

urlpatterns = [
    path(
        'projects/<uuid:project_pk>/candidates/<uuid:candidate_pk>/resume/',
        views.ResumeUploadView.as_view(),
        name='resume-upload',
    ),
    path(
        'projects/<uuid:project_pk>/resumes/bulk/',
        views.BulkResumeUploadView.as_view(),
        name='resume-bulk-upload',
    ),
]
