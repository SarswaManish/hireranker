from django.urls import path

from . import views

urlpatterns = [
    path('submit/', views.CandidateReviewSubmitView.as_view(), name='review-submit'),
    path('<uuid:token>/', views.CandidateReviewGetView.as_view(), name='review-get'),
    path('<uuid:token>/pay/', views.CandidateReviewPayView.as_view(), name='review-pay'),
]
