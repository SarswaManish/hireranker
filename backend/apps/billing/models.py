import uuid

from django.db import models
from django.utils import timezone


class PaymentCustomer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='payment_customer',
    )
    stripe_customer_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_payment_customer'
        verbose_name = 'Payment Customer'
        verbose_name_plural = 'Payment Customers'

    def __str__(self):
        return f"{self.organization.name} - {self.stripe_customer_id}"


class Subscription(models.Model):
    class Plan(models.TextChoices):
        FREE = 'free', 'Free'
        STARTER = 'starter', 'Starter'
        PROFESSIONAL = 'professional', 'Professional'
        ENTERPRISE = 'enterprise', 'Enterprise'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CANCELED = 'canceled', 'Canceled'
        PAST_DUE = 'past_due', 'Past Due'
        TRIALING = 'trialing', 'Trialing'

    # Report limits per plan
    PLAN_LIMITS = {
        Plan.FREE: 10,
        Plan.STARTER: 100,
        Plan.PROFESSIONAL: 500,
        Plan.ENTERPRISE: -1,  # Unlimited
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.FREE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, default='')
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    candidate_reports_used = models.IntegerField(default=0)
    candidate_reports_limit = models.IntegerField(default=10)  # Default free plan
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_subscription'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization.name} - {self.plan} ({self.status})"

    @property
    def is_active(self):
        return self.status in [self.Status.ACTIVE, self.Status.TRIALING]

    @property
    def has_reports_remaining(self):
        if self.candidate_reports_limit == -1:
            return True
        return self.candidate_reports_used < self.candidate_reports_limit

    @property
    def reports_remaining(self):
        if self.candidate_reports_limit == -1:
            return None  # Unlimited
        return max(0, self.candidate_reports_limit - self.candidate_reports_used)


class CandidateReviewPayment(models.Model):
    """
    One-off payment for a candidate self-review report.
    Used for the public-facing /api/review/ endpoint.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, default='', db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='usd')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    report_token = models.UUIDField(unique=True, default=uuid.uuid4, db_index=True)
    resume_text = models.TextField(blank=True, default='')
    jd_text = models.TextField(blank=True, default='')
    report_result = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_candidate_review_payment'
        verbose_name = 'Candidate Review Payment'
        verbose_name_plural = 'Candidate Review Payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.email} - {self.status}"
