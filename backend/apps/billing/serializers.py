from rest_framework import serializers

from .models import PaymentCustomer, Subscription, CandidateReviewPayment


class SubscriptionSerializer(serializers.ModelSerializer):
    reports_remaining = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Subscription
        fields = [
            'id', 'organization', 'plan', 'status',
            'current_period_start', 'current_period_end',
            'candidate_reports_used', 'candidate_reports_limit',
            'reports_remaining', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CandidateReviewSubmitSerializer(serializers.Serializer):
    email = serializers.EmailField()
    resume_text = serializers.CharField(
        min_length=100,
        max_length=50000,
        help_text='Full resume text (extracted from PDF/DOCX or pasted)',
    )
    jd_text = serializers.CharField(
        min_length=50,
        max_length=10000,
        help_text='Job description to evaluate against',
    )


class CandidateReviewPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateReviewPayment
        fields = [
            'id', 'email', 'amount', 'currency', 'status',
            'report_token', 'report_result', 'created_at',
        ]
        read_only_fields = [
            'id', 'stripe_payment_intent_id', 'report_token',
            'report_result', 'created_at',
        ]


class PaymentIntentSerializer(serializers.Serializer):
    client_secret = serializers.CharField()
    payment_intent_id = serializers.CharField()
    report_token = serializers.UUIDField()
    amount = serializers.IntegerField()
    currency = serializers.CharField()
