import logging

from django.db import transaction

from .models import HiringProject

logger = logging.getLogger(__name__)


def get_project_candidate_stats(project: HiringProject) -> dict:
    """
    Return summary stats for a project.
    """
    from apps.candidates.models import Candidate
    from apps.evaluations.models import CandidateEvaluation
    from django.db.models import Avg, Max

    candidates = Candidate.objects.filter(project=project, is_duplicate=False)
    evaluations = CandidateEvaluation.objects.filter(project=project, status='completed')
    agg = evaluations.aggregate(avg=Avg('overall_score'), top=Max('overall_score'))

    return {
        'total_candidates': candidates.count(),
        'evaluated_candidates': evaluations.count(),
        'pending_evaluation': candidates.filter(status__in=['pending', 'evaluating']).count(),
        'average_score': agg['avg'],
        'top_score': agg['top'],
    }
