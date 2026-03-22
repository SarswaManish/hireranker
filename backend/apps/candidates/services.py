import logging

from django.db import transaction

from .models import Candidate, CandidateImportBatch

logger = logging.getLogger(__name__)


@transaction.atomic
def process_import_batch(batch_id: str, column_mapping: dict = None) -> None:
    """
    Process a candidate import batch.
    Updates batch status and imports candidates.
    """
    from .importers import import_candidates_from_file, detect_duplicates

    batch = CandidateImportBatch.objects.select_related('project').get(id=batch_id)
    batch.status = CandidateImportBatch.Status.PROCESSING
    batch.save()

    try:
        processed, failed, errors = import_candidates_from_file(
            batch=batch,
            file=batch.file_path,
            column_mapping=column_mapping or batch.column_mapping or {},
        )

        batch.processed_rows = processed
        batch.failed_rows = failed
        batch.error_log = errors[:100]  # Cap error log at 100 entries
        batch.status = CandidateImportBatch.Status.COMPLETED
        batch.save()

        # Detect duplicates
        detect_duplicates(batch.project)

        from core.utils import log_event, AuditEventType
        if batch.imported_by:
            log_event(batch.imported_by, AuditEventType.CANDIDATES_IMPORTED, {
                'batch_id': str(batch.id),
                'processed': processed,
                'failed': failed,
                'project_id': str(batch.project.id),
            })

        logger.info(
            "Batch %s completed: processed=%d, failed=%d",
            batch_id, processed, failed
        )

    except Exception as e:
        logger.error("Batch %s processing failed: %s", batch_id, e)
        batch.status = CandidateImportBatch.Status.FAILED
        batch.error_log = [{'row': 0, 'error': str(e)}]
        batch.save()
        raise
