import logging

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name='tasks.resume_tasks.parse_resume_task',
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def parse_resume_task(self, resume_id: str) -> dict:
    """
    Parse a single resume file and extract text.

    Args:
        resume_id: UUID string of CandidateResume

    Returns:
        Dict with status and parse_status
    """
    from apps.candidates.models import CandidateResume
    from apps.resumes.parsers import parse_resume

    logger.info("Parsing resume %s", resume_id)

    try:
        resume = CandidateResume.objects.select_related('candidate').get(id=resume_id)
    except CandidateResume.DoesNotExist:
        logger.error("Resume %s not found", resume_id)
        return {'status': 'error', 'message': 'Resume not found'}

    try:
        parse_resume(resume)
        logger.info("Resume %s parsed successfully", resume_id)

        # Trigger evaluation if candidate is ready
        candidate = resume.candidate
        if candidate.status == 'pending' and resume.parse_status == 'completed':
            from apps.candidates.models import Candidate
            candidate.status = Candidate.Status.PARSED
            candidate.save(update_fields=['status'])

            # Auto-trigger evaluation
            evaluate_after_parse.delay(str(candidate.id))

        return {
            'status': 'success',
            'resume_id': resume_id,
            'parse_status': resume.parse_status,
            'text_length': len(resume.raw_text),
        }

    except SoftTimeLimitExceeded:
        logger.error("Resume parsing %s timed out", resume_id)
        resume.parse_status = 'failed'
        resume.parse_error = 'Parsing timed out'
        resume.save(update_fields=['parse_status', 'parse_error'])
        return {'status': 'error', 'message': 'Parsing timed out'}

    except Exception as exc:
        logger.error("Resume parsing %s failed: %s", resume_id, exc)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(
    bind=True,
    name='tasks.resume_tasks.evaluate_after_parse',
)
def evaluate_after_parse(self, candidate_id: str) -> None:
    """Trigger evaluation after resume is parsed."""
    from tasks.evaluation_tasks import evaluate_candidate_task
    evaluate_candidate_task.delay(candidate_id)


@shared_task(
    bind=True,
    name='tasks.resume_tasks.process_candidate_batch',
    max_retries=2,
    default_retry_delay=120,
)
def process_candidate_batch(self, batch_id: str, column_mapping: dict = None) -> dict:
    """
    Process a candidate import batch (CSV/XLSX).

    Args:
        batch_id: UUID string of CandidateImportBatch
        column_mapping: Optional column mapping dict

    Returns:
        Dict with processing results
    """
    from apps.candidates.services import process_import_batch

    logger.info("Processing import batch %s", batch_id)

    try:
        process_import_batch(batch_id, column_mapping=column_mapping or {})
        logger.info("Batch %s processing complete", batch_id)
        return {'status': 'success', 'batch_id': batch_id}

    except SoftTimeLimitExceeded:
        logger.error("Batch processing %s timed out", batch_id)
        from apps.candidates.models import CandidateImportBatch
        try:
            batch = CandidateImportBatch.objects.get(id=batch_id)
            batch.status = CandidateImportBatch.Status.FAILED
            batch.error_log = [{'row': 0, 'error': 'Processing timed out'}]
            batch.save()
        except Exception:
            pass
        return {'status': 'error', 'message': 'Batch processing timed out'}

    except Exception as exc:
        logger.error("Batch %s processing failed: %s", batch_id, exc)
        raise self.retry(exc=exc, countdown=120)


@shared_task(
    bind=True,
    name='tasks.resume_tasks.process_single_candidate_import',
    max_retries=3,
)
def process_single_candidate_import(self, candidate_id: str) -> dict:
    """
    Process a single candidate's resume URL (download and parse).
    Used when candidates are imported with resume URLs.

    Args:
        candidate_id: UUID string of Candidate

    Returns:
        Dict with processing results
    """
    from apps.candidates.models import Candidate, CandidateResume

    logger.info("Processing candidate import %s", candidate_id)

    try:
        candidate = Candidate.objects.get(id=candidate_id)
    except Candidate.DoesNotExist:
        logger.error("Candidate %s not found", candidate_id)
        return {'status': 'error', 'message': 'Candidate not found'}

    if not candidate.resume_url:
        logger.debug("Candidate %s has no resume URL, skipping", candidate_id)
        return {'status': 'skipped', 'reason': 'No resume URL'}

    try:
        # Create or get resume record
        resume, _ = CandidateResume.objects.get_or_create(
            candidate=candidate,
            defaults={
                'file_type': CandidateResume.FileType.URL,
                'file_name': f'resume_from_url_{candidate_id}',
            }
        )
        resume.file_type = CandidateResume.FileType.URL
        resume.parse_status = CandidateResume.ParseStatus.PENDING
        resume.save(update_fields=['file_type', 'parse_status'])

        # Trigger parsing
        parse_resume_task.delay(str(resume.id))

        return {'status': 'queued', 'candidate_id': candidate_id, 'resume_id': str(resume.id)}

    except Exception as exc:
        logger.error("Failed to process candidate %s: %s", candidate_id, exc)
        raise self.retry(exc=exc, countdown=60)
