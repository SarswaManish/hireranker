import logging

from django.conf import settings
from django.db import transaction

from .models import PaymentCustomer, Subscription, CandidateReviewPayment

logger = logging.getLogger(__name__)


def get_or_create_stripe_customer(organization) -> PaymentCustomer:
    """Create or retrieve Stripe customer for an organization."""
    try:
        return organization.payment_customer
    except PaymentCustomer.DoesNotExist:
        pass

    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY

    customer = stripe.Customer.create(
        name=organization.name,
        metadata={'organization_id': str(organization.id)},
    )

    payment_customer = PaymentCustomer.objects.create(
        organization=organization,
        stripe_customer_id=customer.id,
    )
    return payment_customer


def get_active_subscription(organization) -> Subscription | None:
    """Get the active subscription for an organization."""
    return Subscription.objects.filter(
        organization=organization,
        status__in=[Subscription.Status.ACTIVE, Subscription.Status.TRIALING],
    ).order_by('-created_at').first()


def get_or_create_free_subscription(organization) -> Subscription:
    """Get or create a free-tier subscription."""
    sub = Subscription.objects.filter(organization=organization).order_by('-created_at').first()
    if sub:
        return sub

    return Subscription.objects.create(
        organization=organization,
        plan=Subscription.Plan.FREE,
        status=Subscription.Status.ACTIVE,
        candidate_reports_limit=Subscription.PLAN_LIMITS[Subscription.Plan.FREE],
    )


@transaction.atomic
def create_review_payment_intent(email: str, resume_text: str, jd_text: str) -> dict:
    """
    Create a Stripe PaymentIntent for a candidate self-review.

    Returns dict with client_secret, payment_intent_id, report_token.
    """
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY

    amount_cents = getattr(settings, 'CANDIDATE_REVIEW_PRICE_CENTS', 999)

    # Create payment record first
    review = CandidateReviewPayment.objects.create(
        email=email.lower().strip(),
        amount=amount_cents / 100,
        currency='usd',
        resume_text=resume_text[:50000],
        jd_text=jd_text[:10000],
        status=CandidateReviewPayment.Status.PENDING,
    )

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency='usd',
            receipt_email=email,
            metadata={
                'report_token': str(review.report_token),
                'review_id': str(review.id),
            },
        )

        review.stripe_payment_intent_id = intent.id
        review.save(update_fields=['stripe_payment_intent_id'])

        return {
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id,
            'report_token': str(review.report_token),
        }

    except Exception as e:
        logger.error("Failed to create PaymentIntent for %s: %s", email, e)
        review.delete()
        raise


def handle_payment_webhook(event: dict) -> None:
    """Process Stripe webhook events."""
    event_type = event.get('type')
    data_object = event.get('data', {}).get('object', {})

    if event_type == 'payment_intent.succeeded':
        payment_intent_id = data_object.get('id')
        _handle_payment_succeeded(payment_intent_id)

    elif event_type == 'payment_intent.payment_failed':
        payment_intent_id = data_object.get('id')
        _handle_payment_failed(payment_intent_id)

    elif event_type == 'customer.subscription.updated':
        _handle_subscription_updated(data_object)

    elif event_type == 'customer.subscription.deleted':
        _handle_subscription_deleted(data_object)


def _handle_payment_succeeded(payment_intent_id: str) -> None:
    """Mark review payment as completed and trigger report generation."""
    try:
        review = CandidateReviewPayment.objects.get(stripe_payment_intent_id=payment_intent_id)
    except CandidateReviewPayment.DoesNotExist:
        logger.warning("PaymentIntent %s not found in database", payment_intent_id)
        return

    review.status = CandidateReviewPayment.Status.COMPLETED
    review.save(update_fields=['status'])

    # Trigger report generation
    if review.resume_text and review.jd_text:
        from tasks.evaluation_tasks import generate_review_report_task
        generate_review_report_task.delay(str(review.id))

    logger.info("Payment succeeded for review %s", review.id)


def _handle_payment_failed(payment_intent_id: str) -> None:
    try:
        review = CandidateReviewPayment.objects.get(stripe_payment_intent_id=payment_intent_id)
        review.status = CandidateReviewPayment.Status.FAILED
        review.save(update_fields=['status'])
    except CandidateReviewPayment.DoesNotExist:
        pass


def _handle_subscription_updated(subscription_data: dict) -> None:
    stripe_sub_id = subscription_data.get('id')
    stripe_status = subscription_data.get('status', 'active')

    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
        sub.status = stripe_status
        sub.save(update_fields=['status'])
    except Subscription.DoesNotExist:
        pass


def _handle_subscription_deleted(subscription_data: dict) -> None:
    stripe_sub_id = subscription_data.get('id')
    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
        sub.status = Subscription.Status.CANCELED
        sub.save(update_fields=['status'])
    except Subscription.DoesNotExist:
        pass
