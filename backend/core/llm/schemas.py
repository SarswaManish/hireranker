"""
TypedDict schemas for LLM response validation in HireRanker.
"""
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class WorkExperienceSchema:
    company: str = ''
    title: str = ''
    duration: str = ''
    start_date: str = ''
    end_date: str = ''
    description: str = ''
    achievements: List[str] = field(default_factory=list)


@dataclass
class EducationSchema:
    degree: str = ''
    institution: str = ''
    graduation_year: Optional[int] = None
    cgpa_or_percentage: str = ''


@dataclass
class ProjectSchema:
    name: str = ''
    description: str = ''
    technologies: List[str] = field(default_factory=list)
    url: str = ''


@dataclass
class CandidateProfileSchema:
    """Schema for parsed resume -> candidate profile."""
    full_name: str = ''
    email: str = ''
    phone: str = ''
    location: str = ''
    summary: str = ''
    total_experience_years: Optional[float] = None
    skills: List[str] = field(default_factory=list)
    work_experience: List[dict] = field(default_factory=list)
    education: List[dict] = field(default_factory=list)
    projects: List[dict] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    github_url: str = ''
    linkedin_url: str = ''
    portfolio_url: str = ''

    @classmethod
    def from_dict(cls, data: dict) -> 'CandidateProfileSchema':
        return cls(
            full_name=data.get('full_name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            location=data.get('location', ''),
            summary=data.get('summary', ''),
            total_experience_years=data.get('total_experience_years'),
            skills=data.get('skills', []),
            work_experience=data.get('work_experience', []),
            education=data.get('education', []),
            projects=data.get('projects', []),
            certifications=data.get('certifications', []),
            github_url=data.get('github_url', ''),
            linkedin_url=data.get('linkedin_url', ''),
            portfolio_url=data.get('portfolio_url', ''),
        )


@dataclass
class JDRequirementsSchema:
    """Schema for parsed job description requirements."""
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    min_experience_years: Optional[float] = None
    max_experience_years: Optional[float] = None
    education_requirements: str = ''
    responsibilities: List[str] = field(default_factory=list)
    domain_keywords: List[str] = field(default_factory=list)
    seniority_level: str = 'mid'
    location_requirements: str = ''
    required_certifications: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> 'JDRequirementsSchema':
        return cls(
            required_skills=data.get('required_skills', []),
            preferred_skills=data.get('preferred_skills', []),
            min_experience_years=data.get('min_experience_years'),
            max_experience_years=data.get('max_experience_years'),
            education_requirements=data.get('education_requirements', ''),
            responsibilities=data.get('responsibilities', []),
            domain_keywords=data.get('domain_keywords', []),
            seniority_level=data.get('seniority_level', 'mid'),
            location_requirements=data.get('location_requirements', ''),
            required_certifications=data.get('required_certifications', []),
            soft_skills=data.get('soft_skills', []),
        )


@dataclass
class ScoreBreakdownSchema:
    """Schema for individual score dimensions."""
    skills_match_score: float = 0.0
    experience_depth_score: float = 0.0
    impact_score: float = 0.0
    project_relevance_score: float = 0.0
    communication_resume_quality_score: float = 0.0
    domain_fit_score: float = 0.0
    risk_penalty_score: float = 0.0
    skills_match_reasoning: str = ''
    experience_depth_reasoning: str = ''
    impact_reasoning: str = ''
    project_relevance_reasoning: str = ''
    communication_reasoning: str = ''
    domain_fit_reasoning: str = ''
    risk_reasoning: str = ''


@dataclass
class CandidateEvaluationResultSchema:
    """Schema for the full LLM evaluation result."""
    scores: ScoreBreakdownSchema = field(default_factory=ScoreBreakdownSchema)
    candidate_summary: str = ''
    recruiter_takeaway: str = ''
    recommendation: str = 'maybe'
    confidence_level: str = 'medium'
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    notable_projects: List[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> 'CandidateEvaluationResultSchema':
        scores_data = data.get('scores', {})
        scores = ScoreBreakdownSchema(
            skills_match_score=float(scores_data.get('skills_match_score', 0)),
            experience_depth_score=float(scores_data.get('experience_depth_score', 0)),
            impact_score=float(scores_data.get('impact_score', 0)),
            project_relevance_score=float(scores_data.get('project_relevance_score', 0)),
            communication_resume_quality_score=float(scores_data.get('communication_resume_quality_score', 0)),
            domain_fit_score=float(scores_data.get('domain_fit_score', 0)),
            risk_penalty_score=float(scores_data.get('risk_penalty_score', 0)),
            skills_match_reasoning=str(scores_data.get('skills_match_reasoning', '')),
            experience_depth_reasoning=str(scores_data.get('experience_depth_reasoning', '')),
            impact_reasoning=str(scores_data.get('impact_reasoning', '')),
            project_relevance_reasoning=str(scores_data.get('project_relevance_reasoning', '')),
            communication_reasoning=str(scores_data.get('communication_reasoning', '')),
            domain_fit_reasoning=str(scores_data.get('domain_fit_reasoning', '')),
            risk_reasoning=str(scores_data.get('risk_reasoning', '')),
        )
        return cls(
            scores=scores,
            candidate_summary=data.get('candidate_summary', ''),
            recruiter_takeaway=data.get('recruiter_takeaway', ''),
            recommendation=data.get('recommendation', 'maybe'),
            confidence_level=data.get('confidence_level', 'medium'),
            strengths=data.get('strengths', []),
            weaknesses=data.get('weaknesses', []),
            missing_requirements=data.get('missing_requirements', []),
            red_flags=data.get('red_flags', []),
            notable_projects=data.get('notable_projects', []),
        )


@dataclass
class CandidateComparisonResultSchema:
    """Schema for candidate comparison result."""
    winner: str = 'tie'  # 'A', 'B', or 'tie'
    winner_name: str = ''
    margin: str = 'slight'  # 'slight', 'moderate', 'clear'
    reasoning: str = ''
    candidate_a_advantages: List[str] = field(default_factory=list)
    candidate_b_advantages: List[str] = field(default_factory=list)
    scenario_prefer_a: str = ''
    scenario_prefer_b: str = ''
    recommendation: str = ''

    @classmethod
    def from_dict(cls, data: dict) -> 'CandidateComparisonResultSchema':
        return cls(
            winner=data.get('winner', 'tie'),
            winner_name=data.get('winner_name', ''),
            margin=data.get('margin', 'slight'),
            reasoning=data.get('reasoning', ''),
            candidate_a_advantages=data.get('candidate_a_advantages', []),
            candidate_b_advantages=data.get('candidate_b_advantages', []),
            scenario_prefer_a=data.get('scenario_prefer_a', ''),
            scenario_prefer_b=data.get('scenario_prefer_b', ''),
            recommendation=data.get('recommendation', ''),
        )


@dataclass
class ResumeFeedbackResultSchema:
    """Schema for resume feedback result."""
    overall_quality_score: float = 0.0
    ats_score: float = 0.0
    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    missing_sections: List[str] = field(default_factory=list)
    weak_bullets: List[str] = field(default_factory=list)
    quantification_score: float = 0.0
    keyword_gaps: List[str] = field(default_factory=list)
    executive_summary: str = ''

    @classmethod
    def from_dict(cls, data: dict) -> 'ResumeFeedbackResultSchema':
        return cls(
            overall_quality_score=float(data.get('overall_quality_score', 0)),
            ats_score=float(data.get('ats_score', 0)),
            strengths=data.get('strengths', []),
            improvements=data.get('improvements', []),
            missing_sections=data.get('missing_sections', []),
            weak_bullets=data.get('weak_bullets', []),
            quantification_score=float(data.get('quantification_score', 0)),
            keyword_gaps=data.get('keyword_gaps', []),
            executive_summary=data.get('executive_summary', ''),
        )
