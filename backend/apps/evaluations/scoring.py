"""
Scoring framework for candidate evaluations.
Implements weighted scoring across multiple dimensions.
"""

SCORE_WEIGHTS = {
    'skills_match': 0.30,
    'experience_depth': 0.20,
    'impact': 0.15,
    'project_relevance': 0.15,
    'communication': 0.10,
    'domain_fit': 0.10,
}

# Score thresholds for recommendation buckets
RECOMMENDATION_THRESHOLDS = {
    'strong_yes': 80.0,
    'yes': 65.0,
    'maybe': 45.0,
    'no': 0.0,
}


def calculate_overall_score(score_breakdown) -> float:
    """
    Calculate overall weighted score from a CandidateScoreBreakdown instance or dict.

    Each dimension is scored 0-100. The weighted average gives the overall score.
    The risk_penalty_score is subtracted (0-20 points max penalty).

    Args:
        score_breakdown: CandidateScoreBreakdown instance or dict with score fields

    Returns:
        Float score 0-100
    """
    if hasattr(score_breakdown, '__dict__'):
        # ORM model instance
        scores = {
            'skills_match': getattr(score_breakdown, 'skills_match_score', 0) or 0,
            'experience_depth': getattr(score_breakdown, 'experience_depth_score', 0) or 0,
            'impact': getattr(score_breakdown, 'impact_score', 0) or 0,
            'project_relevance': getattr(score_breakdown, 'project_relevance_score', 0) or 0,
            'communication': getattr(score_breakdown, 'communication_resume_quality_score', 0) or 0,
            'domain_fit': getattr(score_breakdown, 'domain_fit_score', 0) or 0,
        }
        risk_penalty = getattr(score_breakdown, 'risk_penalty_score', 0) or 0
    else:
        # Dict
        scores = {
            'skills_match': score_breakdown.get('skills_match_score', 0) or 0,
            'experience_depth': score_breakdown.get('experience_depth_score', 0) or 0,
            'impact': score_breakdown.get('impact_score', 0) or 0,
            'project_relevance': score_breakdown.get('project_relevance_score', 0) or 0,
            'communication': score_breakdown.get('communication_resume_quality_score', 0) or 0,
            'domain_fit': score_breakdown.get('domain_fit_score', 0) or 0,
        }
        risk_penalty = score_breakdown.get('risk_penalty_score', 0) or 0

    # Clamp each score 0-100
    for key in scores:
        scores[key] = max(0.0, min(100.0, float(scores[key])))

    # Weighted sum
    weighted_sum = sum(scores[dim] * SCORE_WEIGHTS[dim] for dim in SCORE_WEIGHTS)

    # Apply risk penalty (capped at 20 points)
    risk_deduction = max(0.0, min(20.0, float(risk_penalty)))

    final_score = weighted_sum - risk_deduction
    return round(max(0.0, min(100.0, final_score)), 2)


def get_recommendation_bucket(score: float) -> str:
    """
    Map a numeric score to a recommendation bucket.

    Args:
        score: Float score 0-100

    Returns:
        One of: 'strong_yes', 'yes', 'maybe', 'no'
    """
    if score >= RECOMMENDATION_THRESHOLDS['strong_yes']:
        return 'strong_yes'
    elif score >= RECOMMENDATION_THRESHOLDS['yes']:
        return 'yes'
    elif score >= RECOMMENDATION_THRESHOLDS['maybe']:
        return 'maybe'
    else:
        return 'no'


def normalize_score_dict(raw_scores: dict) -> dict:
    """
    Normalize raw score dict from LLM output to 0-100 scale.
    Handles both 0-10 and 0-100 input scales.

    Args:
        raw_scores: Dict with score values

    Returns:
        Normalized dict with 0-100 values
    """
    score_keys = [
        'skills_match_score',
        'experience_depth_score',
        'impact_score',
        'project_relevance_score',
        'communication_resume_quality_score',
        'domain_fit_score',
        'risk_penalty_score',
    ]

    normalized = {}
    for key in score_keys:
        val = raw_scores.get(key, 0)
        try:
            val = float(val)
        except (TypeError, ValueError):
            val = 0.0

        # If scores appear to be on 0-10 scale, convert to 0-100
        if val <= 10.0 and key != 'risk_penalty_score':
            val = val * 10

        normalized[key] = round(max(0.0, min(100.0, val)), 2)

    return normalized
