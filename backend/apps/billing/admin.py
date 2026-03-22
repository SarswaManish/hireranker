from django.contrib import admin

from .models import PaymentCustomer, Subscription, CandidateReviewPayment


@admin.register(PaymentCustomer)
class PaymentCustomerAdmin(admin.ModelAdmin):
    list_display = ['organization', 'stripe_customer_id', 'created_at']
    search_fields = ['organization__name', 'stripe_customer_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['organization']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'organization', 'plan', 'status',
        'candidate_reports_used', 'candidate_reports_limit',
        'current_period_end', 'created_at',
    ]
    list_filter = ['plan', 'status', 'created_at']
    search_fields = ['organization__name', 'stripe_subscription_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['organization']


@admin.register(CandidateReviewPayment)
class CandidateReviewPaymentAdmin(admin.ModelAdmin):
    list_display = ['email', 'amount', 'currency', 'status', 'stripe_payment_intent_id', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['email', 'stripe_payment_intent_id']
    readonly_fields = ['id', 'report_token', 'created_at', 'updated_at']
