from django.urls import path

from . import views

urlpatterns = [
    path('organizations/<uuid:org_id>/subscription/', views.SubscriptionView.as_view(), name='billing-subscription'),
    path('webhook/stripe/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
]
