import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subscription, CandidateReviewPayment
from .serializers import (
    SubscriptionSerializer,
    CandidateReviewSubmitSerializer,
    CandidateReviewPaymentSerializer,
    PaymentIntentSerializer,
)
from .services import get_or_create_free_subscription, create_review_payment_intent
from apps.organizations.models import Organization, Membership

logger = logging.getLogger(__name__)


class SubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, org_id=None):
        org = get_object_or_404(Organization, id=org_id)
        membership = Membership.objects.filter(
            user=request.user, organization=org, is_active=True
        ).first()
        if not membership:
            return Response(
                {'data': None, 'message': 'Access denied', 'errors': None},
                status=status.HTTP_403_FORBIDDEN
            )

        subscription = get_or_create_free_subscription(org)
        return Response(
            {'data': SubscriptionSerializer(subscription).data, 'message': None, 'errors': None}
        )


class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

        if webhook_secret:
            try:
                event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            except stripe.error.SignatureVerificationError as e:
                logger.warning("Stripe webhook signature verification failed: %s", e)
                return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            import json
            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)

        from .services import handle_payment_webhook
        try:
            handle_payment_webhook(event)
        except Exception as e:
            logger.error("Webhook handler error: %s", e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'received': True})


# Public candidate review endpoints
class CandidateReviewSubmitView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CandidateReviewSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        validated = serializer.validated_data

        # Create payment intent if Stripe is configured
        if settings.STRIPE_SECRET_KEY:
            try:
                payment_data = create_review_payment_intent(
                    email=validated['email'],
                    resume_text=validated['resume_text'],
                    jd_text=validated['jd_text'],
                )
                return Response(
                    {
                        'data': {
                            **payment_data,
                            'amount': getattr(settings, 'CANDIDATE_REVIEW_PRICE_CENTS', 999),
                            'currency': 'usd',
                        },
                        'message': 'Payment intent created. Complete payment to get your report.',
                        'errors': None,
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                logger.error("Failed to create review payment: %s", e)
                return Response(
                    {'data': None, 'message': 'Failed to create payment', 'errors': None},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # No Stripe configured - generate report directly (dev mode)
            from .models import CandidateReviewPayment
            review = CandidateReviewPayment.objects.create(
                email=validated['email'].lower(),
                amount=0,
                status=CandidateReviewPayment.Status.COMPLETED,
                resume_text=validated['resume_text'],
                jd_text=validated['jd_text'],
            )
            from tasks.evaluation_tasks import generate_review_report_task
            generate_review_report_task.delay(str(review.id))
            return Response(
                {
                    'data': {
                        'report_token': str(review.report_token),
                        'message': 'Report generation started (dev mode - no payment required)',
                    },
                    'message': 'Report queued',
                    'errors': None,
                },
                status=status.HTTP_201_CREATED
            )


class CandidateReviewGetView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token=None):
        review = get_object_or_404(CandidateReviewPayment, report_token=token)

        if review.status not in [CandidateReviewPayment.Status.COMPLETED]:
            # Return partial/preview data
            return Response(
                {
                    'data': {
                        'status': review.status,
                        'report_token': str(review.report_token),
                        'preview': 'Payment required to view full report',
                        'amount': str(review.amount),
                        'currency': review.currency,
                    },
                    'message': 'Payment required',
                    'errors': None,
                },
                status=status.HTTP_402_PAYMENT_REQUIRED
            )

        return Response(
            {
                'data': {
                    'status': review.status,
                    'report_token': str(review.report_token),
                    'report': review.report_result,
                    'email': review.email,
                },
                'message': None,
                'errors': None,
            }
        )


class CandidateReviewPayView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, token=None):
        """Create/retrieve payment intent for a review token."""
        review = get_object_or_404(CandidateReviewPayment, report_token=token)

        if review.status == CandidateReviewPayment.Status.COMPLETED:
            return Response(
                {'data': {'status': 'already_paid', 'report_token': str(review.report_token)}, 'message': 'Already paid', 'errors': None},
                status=status.HTTP_200_OK
            )

        if not settings.STRIPE_SECRET_KEY:
            return Response(
                {'data': None, 'message': 'Payment not configured', 'errors': None},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        amount_cents = getattr(settings, 'CANDIDATE_REVIEW_PRICE_CENTS', 999)

        if review.stripe_payment_intent_id:
            try:
                intent = stripe.PaymentIntent.retrieve(review.stripe_payment_intent_id)
                return Response(
                    {
                        'data': {
                            'client_secret': intent.client_secret,
                            'payment_intent_id': intent.id,
                            'amount': amount_cents,
                        },
                        'message': None,
                        'errors': None,
                    }
                )
            except Exception:
                pass

        # Create new intent
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency='usd',
            receipt_email=review.email,
            metadata={
                'report_token': str(review.report_token),
                'review_id': str(review.id),
            },
        )
        review.stripe_payment_intent_id = intent.id
        review.save(update_fields=['stripe_payment_intent_id'])

        return Response(
            {
                'data': {
                    'client_secret': intent.client_secret,
                    'payment_intent_id': intent.id,
                    'amount': amount_cents,
                },
                'message': None,
                'errors': None,
            },
            status=status.HTTP_201_CREATED
        )
