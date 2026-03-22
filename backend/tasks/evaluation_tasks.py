import logging

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name='tasks.evaluation_tasks.evaluate_candidate_task',
    max_retries=3,
    default_retry_delay=60,
)
def evaluate_candidate_task(self, candidate_id: str) -> dict:
    """
    Evaluate a single candidate using LLM.

    Args:
        candidate_id: UUID string of Candidate

    Returns:
        Dict with evaluation results
    """
    from apps.candidates.models import Candidate
    from apps.evaluations.services import evaluate_candidate

    logger.info("Evaluating candidate %s", candidate_id)

    try:
        candidate = Candidate.objects.select_related('project', 'project__organization').get(
            id=candidate_id
        )
    except Candidate.DoesNotExist:
        logger.error("Candidate %s not found", candidate_id)
        return {'status': 'error', 'message': 'Candidate not found'}

    # Skip if already completed
    from apps.evaluations.models import CandidateEvaluation
    existing = CandidateEvaluation.objects.filter(
        candidate=candidate,
        status=CandidateEvaluation.Status.COMPLETED,
    ).first()
    if existing:
        logger.info("Candidate %s already evaluated, skipping", candidate_id)
        return {
            'status': 'skipped',
            'candidate_id': candidate_id,
            'evaluation_id': str(existing.id),
        }

    try:
        evaluation = evaluate_candidate(candidate)
        return {
            'status': 'success',
            'candidate_id': candidate_id,
            'evaluation_id': str(evaluation.id),
            'score': evaluation.overall_score,
            'recommendation': evaluation.recommendation,
        }

    except SoftTimeLimitExceeded:
        logger.error("Evaluation of candidate %s timed out", candidate_id)
        return {'status': 'error', 'message': 'Evaluation timed out'}

    except Exception as exc:
        logger.error("Evaluation of candidate %s failed: %s", candidate_id, exc)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(
    bind=True,
    name='tasks.evaluation_tasks.evaluate_project_candidates_task',
    max_retries=1,
)
def evaluate_project_candidates_task(self, project_id: str) -> dict:
    """
    Trigger evaluation for all eligible candidates in a project.

    Args:
        project_id: UUID string of HiringProject

    Returns:
        Dict with count of triggered evaluations
    """
    from apps.projects.models import HiringProject
    from apps.candidates.models import Candidate

    logger.info("Triggering project-wide evaluation for project %s", project_id)

    try:
        project = HiringProject.objects.get(id=project_id)
    except HiringProject.DoesNotExist:
        logger.error("Project %s not found", project_id)
        return {'status': 'error', 'message': 'Project not found'}

    candidates = Candidate.objects.filter(
        project=project,
        is_duplicate=False,
        status__in=[Candidate.Status.PENDING, Candidate.Status.PARSED],
    ).values_list('id', flat=True)

    count = 0
    for candidate_id in candidates:
        evaluate_candidate_task.delay(str(candidate_id))
        count += 1

    logger.info("Triggered %d evaluations for project %s", count, project_id)
    return {'status': 'success', 'project_id': project_id, 'triggered_count': count}


@shared_task(
    bind=True,
    name='tasks.evaluation_tasks.answer_recruiter_query_task',
    max_retries=2,
    default_retry_delay=30,
)
def answer_recruiter_query_task(self, query_id: str) -> dict:
    """
    Answer a recruiter's natural language query asynchronously.

    Args:
        query_id: UUID string of RecruiterQueryHistory

    Returns:
        Dict with response status
    """
    from apps.evaluations.models import RecruiterQueryHistory
    from apps.evaluations.services import answer_recruiter_query

    logger.info("Answering recruiter query %s", query_id)

    try:
        query = RecruiterQueryHistory.objects.select_related('project').get(id=query_id)
    except RecruiterQueryHistory.DoesNotExist:
        logger.error("RecruiterQuery %s not found", query_id)
        return {'status': 'error', 'message': 'Query not found'}

    try:
        answer_recruiter_query(query)
        return {
            'status': 'success',
            'query_id': query_id,
            'response_length': len(query.response_text),
        }

    except SoftTimeLimitExceeded:
        logger.error("Recruiter query %s timed out", query_id)
        query.response_text = "Sorry, the query timed out. Please try again."
        query.save(update_fields=['response_text'])
        return {'status': 'error', 'message': 'Query timed out'}

    except Exception as exc:
        logger.error("Recruiter query %s failed: %s", query_id, exc)
        raise self.retry(exc=exc, countdown=30)


@shared_task(
    bind=True,
    name='tasks.evaluation_tasks.generate_review_report_task',
    max_retries=3,
    default_retry_delay=60,
)
def generate_review_report_task(self, review_id: str) -> dict:
    """
    Generate a candidate self-review report after payment.

    Args:
        review_id: UUID string of CandidateReviewPayment

    Returns:
        Dict with generation results
    """
    from apps.billing.models import CandidateReviewPayment
    from core.llm.client import get_llm_client
    from core.llm.prompts import GenerateResumeFeedbackPrompt

    logger.info("Generating review report for payment %s", review_id)

    try:
        review = CandidateReviewPayment.objects.get(id=review_id)
    except CandidateReviewPayment.DoesNotExist:
        logger.error("Review payment %s not found", review_id)
        return {'status': 'error', 'message': 'Review not found'}

    if review.status != CandidateReviewPayment.Status.COMPLETED:
        logger.warning("Review %s payment not completed, skipping report generation", review_id)
        return {'status': 'skipped', 'reason': 'Payment not completed'}

    try:
        client = get_llm_client()
        prompt = GenerateResumeFeedbackPrompt()

        messages = [
            {'role': 'system', 'content': prompt.system_prompt()},
            {
                'role': 'user',
                'content': prompt.user_prompt(
                    resume_text=review.resume_text,
                    job_description=review.jd_text,
                ),
            },
        ]

        response = client.complete_with_retry(
            messages=messages,
            temperature=0.2,
            max_tokens=3000,
            response_format={'type': 'json_object'},
        )

        report_result = client.parse_json_response(response)
        review.report_result = report_result
        review.save(update_fields=['report_result'])

        logger.info("Review report generated for payment %s", review_id)
        return {
            'status': 'success',
            'review_id': review_id,
            'report_token': str(review.report_token),
        }

    except SoftTimeLimitExceeded:
        logger.error("Review report generation for %s timed out", review_id)
        return {'status': 'error', 'message': 'Report generation timed out'}

    except Exception as exc:
        logger.error("Review report generation %s failed: %s", review_id, exc)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
