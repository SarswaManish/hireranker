import json
import logging
from typing import Optional

from django.db import transaction
from django.utils import timezone

from .models import CandidateEvaluation, CandidateScoreBreakdown, RecruiterQueryHistory
from .scoring import calculate_overall_score, get_recommendation_bucket, normalize_score_dict

logger = logging.getLogger(__name__)

PROMPT_VERSION = '1.0'


def parse_jd_requirements(project) -> 'JobDescriptionSnapshot':
    """
    Parse job description using LLM and create a JD snapshot.

    Args:
        project: HiringProject instance

    Returns:
        JobDescriptionSnapshot with structured requirements
    """
    from apps.projects.models import JobDescriptionSnapshot
    from core.llm.client import get_llm_client
    from core.llm.prompts import ParseJDPrompt

    client = get_llm_client()
    prompt = ParseJDPrompt()

    messages = [
        {'role': 'system', 'content': prompt.system_prompt()},
        {'role': 'user', 'content': prompt.user_prompt(project.job_description)},
    ]

    response = client.complete_with_retry(
        messages=messages,
        temperature=0.1,
        max_tokens=2000,
        response_format={'type': 'json_object'},
    )

    structured = client.parse_json_response(response)

    snapshot = JobDescriptionSnapshot.objects.create(
        project=project,
        raw_text=project.job_description,
        structured_requirements=structured,
        parsed_at=timezone.now(),
        parser_version=PROMPT_VERSION,
    )

    logger.info("JD parsed for project %s, snapshot %s created", project.id, snapshot.id)
    return snapshot


@transaction.atomic
def evaluate_candidate(candidate) -> CandidateEvaluation:
    """
    Run LLM evaluation for a single candidate.

    Args:
        candidate: Candidate instance

    Returns:
        CandidateEvaluation instance
    """
    from apps.candidates.models import Candidate
    from core.llm.client import get_llm_client
    from core.llm.prompts import EvaluateCandidatePrompt

    # Get or create evaluation
    evaluation, _ = CandidateEvaluation.objects.get_or_create(
        candidate=candidate,
        project=candidate.project,
        defaults={'status': CandidateEvaluation.Status.PENDING},
    )

    evaluation.status = CandidateEvaluation.Status.RUNNING
    evaluation.save(update_fields=['status'])

    try:
        project = candidate.project

        # Get latest JD snapshot
        jd_snapshot = project.jd_snapshots.first()
        jd_requirements = jd_snapshot.structured_requirements if jd_snapshot else {}

        # Get resume text
        resume_text = ''
        try:
            resume_text = candidate.resume.raw_text
        except Exception:
            pass

        # Build candidate profile
        candidate_profile = _build_candidate_profile(candidate, resume_text)

        client = get_llm_client()
        prompt = EvaluateCandidatePrompt()

        messages = [
            {'role': 'system', 'content': prompt.system_prompt()},
            {
                'role': 'user',
                'content': prompt.user_prompt(
                    candidate_profile=candidate_profile,
                    jd_requirements=jd_requirements,
                    job_description=project.job_description,
                    must_have_skills=project.must_have_skills,
                    good_to_have_skills=project.good_to_have_skills,
                    role_title=project.role_title,
                ),
            },
        ]

        response = client.complete_with_retry(
            messages=messages,
            temperature=0.2,
            max_tokens=4000,
            response_format={'type': 'json_object'},
        )

        result = client.parse_json_response(response)

        # Save evaluation
        _save_evaluation_result(evaluation, result, response['model'])

        # Update candidate status
        candidate.status = Candidate.Status.COMPLETED
        candidate.save(update_fields=['status'])

        logger.info(
            "Evaluation completed for candidate %s: score=%.1f, recommendation=%s",
            candidate.id, evaluation.overall_score, evaluation.recommendation
        )

        from core.utils import log_event, AuditEventType
        from apps.evaluations.models import CandidateEvaluation as CE
        # note: candidate.project.created_by may be None
        if project.created_by:
            log_event(project.created_by, AuditEventType.EVALUATION_COMPLETED, {
                'candidate_id': str(candidate.id),
                'evaluation_id': str(evaluation.id),
                'score': evaluation.overall_score,
            })

        return evaluation

    except Exception as e:
        logger.error("Evaluation failed for candidate %s: %s", candidate.id, e)
        evaluation.status = CandidateEvaluation.Status.FAILED
        evaluation.evaluation_error = str(e)
        evaluation.save(update_fields=['status', 'evaluation_error'])

        from apps.candidates.models import Candidate as C
        candidate.status = C.Status.FAILED
        candidate.save(update_fields=['status'])
        raise


def _build_candidate_profile(candidate, resume_text: str) -> dict:
    """Build a structured candidate profile dict for the prompt."""
    return {
        'name': candidate.name,
        'email': candidate.email,
        'location': candidate.location,
        'college': candidate.college,
        'degree': candidate.degree,
        'graduation_year': candidate.graduation_year,
        'cgpa': str(candidate.cgpa) if candidate.cgpa else '',
        'skills': candidate.skills,
        'github_url': candidate.github_url,
        'linkedin_url': candidate.linkedin_url,
        'portfolio_url': candidate.portfolio_url,
        'resume_text': resume_text[:8000] if resume_text else '',  # Cap at 8k chars
    }


def _save_evaluation_result(evaluation, result: dict, model_used: str) -> None:
    """Save LLM result to evaluation and score breakdown models."""
    raw_scores = result.get('scores', {})
    normalized_scores = normalize_score_dict(raw_scores)

    # Calculate final score
    overall_score = calculate_overall_score(normalized_scores)
    recommendation = result.get('recommendation') or get_recommendation_bucket(overall_score)

    # Validate recommendation
    valid_recs = {'strong_yes', 'yes', 'maybe', 'no'}
    if recommendation not in valid_recs:
        recommendation = get_recommendation_bucket(overall_score)

    evaluation.status = CandidateEvaluation.Status.COMPLETED
    evaluation.overall_score = overall_score
    evaluation.recommendation = recommendation
    evaluation.candidate_summary = result.get('candidate_summary', '')[:2000]
    evaluation.recruiter_takeaway = result.get('recruiter_takeaway', '')[:1000]
    evaluation.confidence_level = result.get('confidence_level', 'medium')
    evaluation.strengths = result.get('strengths', [])[:10]
    evaluation.weaknesses = result.get('weaknesses', [])[:10]
    evaluation.missing_requirements = result.get('missing_requirements', [])[:10]
    evaluation.red_flags = result.get('red_flags', [])[:10]
    evaluation.notable_projects = result.get('notable_projects', [])[:5]
    evaluation.llm_model_used = model_used
    evaluation.prompt_version = PROMPT_VERSION
    evaluation.raw_llm_response = result
    evaluation.evaluated_at = timezone.now()

    evaluation.save()

    # Create or update score breakdown
    CandidateScoreBreakdown.objects.update_or_create(
        evaluation=evaluation,
        defaults={
            'skills_match_score': normalized_scores.get('skills_match_score', 0),
            'experience_depth_score': normalized_scores.get('experience_depth_score', 0),
            'impact_score': normalized_scores.get('impact_score', 0),
            'project_relevance_score': normalized_scores.get('project_relevance_score', 0),
            'communication_resume_quality_score': normalized_scores.get('communication_resume_quality_score', 0),
            'domain_fit_score': normalized_scores.get('domain_fit_score', 0),
            'risk_penalty_score': normalized_scores.get('risk_penalty_score', 0),
            'skills_match_reasoning': raw_scores.get('skills_match_reasoning', ''),
            'experience_depth_reasoning': raw_scores.get('experience_depth_reasoning', ''),
            'impact_reasoning': raw_scores.get('impact_reasoning', ''),
            'project_relevance_reasoning': raw_scores.get('project_relevance_reasoning', ''),
            'communication_reasoning': raw_scores.get('communication_reasoning', ''),
            'domain_fit_reasoning': raw_scores.get('domain_fit_reasoning', ''),
            'risk_reasoning': raw_scores.get('risk_reasoning', ''),
        }
    )


def batch_evaluate_project(project) -> int:
    """
    Trigger evaluation for all eligible candidates in a project.

    Args:
        project: HiringProject instance

    Returns:
        Number of evaluations triggered
    """
    from apps.candidates.models import Candidate
    from tasks.evaluation_tasks import evaluate_candidate_task

    candidates = Candidate.objects.filter(
        project=project,
        is_duplicate=False,
        status__in=[Candidate.Status.PENDING, Candidate.Status.PARSED],
    ).values_list('id', flat=True)

    count = 0
    for candidate_id in candidates:
        evaluate_candidate_task.delay(str(candidate_id))
        count += 1

    logger.info("Triggered %d evaluations for project %s", count, project.id)

    from core.utils import log_event, AuditEventType
    if project.created_by:
        log_event(project.created_by, AuditEventType.EVALUATION_STARTED, {
            'project_id': str(project.id),
            'count': count,
        })

    return count


def calculate_weighted_score(scores: dict) -> float:
    """
    Calculate overall weighted score from a raw scores dict.
    Public API for external use.
    """
    normalized = normalize_score_dict(scores)
    return calculate_overall_score(normalized)


def answer_recruiter_query(query: RecruiterQueryHistory) -> RecruiterQueryHistory:
    """
    Answer a recruiter's natural language query about candidates.

    Args:
        query: RecruiterQueryHistory instance

    Returns:
        Updated RecruiterQueryHistory with response
    """
    from core.llm.client import get_llm_client
    from core.llm.prompts import RecruiterQueryPrompt
    from apps.candidates.models import Candidate
    from apps.evaluations.models import CandidateEvaluation

    client = get_llm_client()
    prompt = RecruiterQueryPrompt()

    project = query.project

    # Get top candidates with evaluations
    candidates = Candidate.objects.filter(
        project=project,
        is_duplicate=False,
        evaluations__status='completed',
    ).select_related('evaluations').prefetch_related('evaluations').order_by(
        '-evaluations__overall_score'
    ).distinct()[:20]

    candidate_summaries = []
    for c in candidates:
        eval_ = c.evaluations.filter(status='completed').first()
        if eval_:
            candidate_summaries.append({
                'id': str(c.id),
                'name': c.name,
                'score': eval_.overall_score,
                'recommendation': eval_.recommendation,
                'summary': eval_.candidate_summary[:500],
                'strengths': eval_.strengths[:3],
                'skills': c.skills[:10],
                'location': c.location,
                'college': c.college,
            })

    messages = [
        {'role': 'system', 'content': prompt.system_prompt()},
        {
            'role': 'user',
            'content': prompt.user_prompt(
                query=query.query_text,
                role_title=project.role_title,
                candidates=candidate_summaries,
            ),
        },
    ]

    try:
        response = client.complete_with_retry(
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )

        result_text = response['content']
        candidate_ids = [str(c.id) for c in candidates[:5]]

        query.response_text = result_text
        query.candidates_referenced = candidate_ids
        query.save(update_fields=['response_text', 'candidates_referenced'])

    except Exception as e:
        logger.error("Failed to answer recruiter query %s: %s", query.id, e)
        query.response_text = f"Sorry, I couldn't process your query: {str(e)}"
        query.save(update_fields=['response_text'])

    return query
