import csv
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def export_rankings_to_csv(project) -> bytes:
    """
    Export ranked candidate data to CSV format.

    Args:
        project: HiringProject instance

    Returns:
        CSV content as bytes
    """
    from apps.evaluations.models import CandidateEvaluation

    evaluations = CandidateEvaluation.objects.filter(
        project=project,
        status=CandidateEvaluation.Status.COMPLETED,
        candidate__is_duplicate=False,
    ).select_related(
        'candidate', 'score_breakdown'
    ).order_by('-overall_score')

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'Rank',
        'Name',
        'Email',
        'Phone',
        'Location',
        'College',
        'Degree',
        'Graduation Year',
        'CGPA',
        'Skills',
        'LinkedIn',
        'GitHub',
        'Portfolio',
        'Resume URL',
        'Overall Score',
        'Recommendation',
        'Confidence Level',
        'Candidate Summary',
        'Recruiter Takeaway',
        'Strengths',
        'Weaknesses',
        'Missing Requirements',
        'Red Flags',
        'Skills Match Score',
        'Experience Depth Score',
        'Impact Score',
        'Project Relevance Score',
        'Communication Score',
        'Domain Fit Score',
        'Risk Penalty Score',
    ])

    for rank, evaluation in enumerate(evaluations, start=1):
        candidate = evaluation.candidate
        breakdown = getattr(evaluation, 'score_breakdown', None)

        writer.writerow([
            rank,
            candidate.name,
            candidate.email,
            candidate.phone,
            candidate.location,
            candidate.college,
            candidate.degree,
            candidate.graduation_year or '',
            str(candidate.cgpa) if candidate.cgpa else '',
            ', '.join(candidate.skills) if candidate.skills else '',
            candidate.linkedin_url,
            candidate.github_url,
            candidate.portfolio_url,
            candidate.resume_url,
            round(evaluation.overall_score, 2) if evaluation.overall_score else '',
            evaluation.get_recommendation_display() if evaluation.recommendation else '',
            evaluation.confidence_level or '',
            evaluation.candidate_summary or '',
            evaluation.recruiter_takeaway or '',
            '; '.join(evaluation.strengths) if evaluation.strengths else '',
            '; '.join(evaluation.weaknesses) if evaluation.weaknesses else '',
            '; '.join(evaluation.missing_requirements) if evaluation.missing_requirements else '',
            '; '.join(evaluation.red_flags) if evaluation.red_flags else '',
            round(breakdown.skills_match_score, 2) if breakdown else '',
            round(breakdown.experience_depth_score, 2) if breakdown else '',
            round(breakdown.impact_score, 2) if breakdown else '',
            round(breakdown.project_relevance_score, 2) if breakdown else '',
            round(breakdown.communication_resume_quality_score, 2) if breakdown else '',
            round(breakdown.domain_fit_score, 2) if breakdown else '',
            round(breakdown.risk_penalty_score, 2) if breakdown else '',
        ])

    return output.getvalue().encode('utf-8')


def export_candidates_to_csv(project, include_unevaluated: bool = False) -> bytes:
    """
    Export all candidates to CSV (with or without evaluation data).

    Args:
        project: HiringProject instance
        include_unevaluated: If True, include candidates without evaluations

    Returns:
        CSV content as bytes
    """
    from apps.candidates.models import Candidate
    from apps.evaluations.models import CandidateEvaluation

    candidates = Candidate.objects.filter(
        project=project,
        is_duplicate=False,
    ).prefetch_related('evaluations', 'tags').order_by('-created_at')

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Name', 'Email', 'Phone', 'Location', 'College', 'Degree',
        'Graduation Year', 'CGPA', 'Skills', 'LinkedIn', 'GitHub',
        'Portfolio', 'Resume URL', 'Tags', 'Status',
        'Overall Score', 'Recommendation',
    ])

    for candidate in candidates:
        evaluation = candidate.evaluations.filter(status='completed').first()
        tags = ', '.join([t.tag for t in candidate.tags.all()])

        writer.writerow([
            candidate.name,
            candidate.email,
            candidate.phone,
            candidate.location,
            candidate.college,
            candidate.degree,
            candidate.graduation_year or '',
            str(candidate.cgpa) if candidate.cgpa else '',
            ', '.join(candidate.skills) if candidate.skills else '',
            candidate.linkedin_url,
            candidate.github_url,
            candidate.portfolio_url,
            candidate.resume_url,
            tags,
            candidate.status,
            round(evaluation.overall_score, 2) if evaluation and evaluation.overall_score else '',
            evaluation.recommendation if evaluation else '',
        ])

    return output.getvalue().encode('utf-8')
