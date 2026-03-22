import uuid

from django.db import models
from django.utils import timezone


class CandidateEvaluation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    class Recommendation(models.TextChoices):
        STRONG_YES = 'strong_yes', 'Strong Yes'
        YES = 'yes', 'Yes'
        MAYBE = 'maybe', 'Maybe'
        NO = 'no', 'No'

    class ConfidenceLevel(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.CASCADE,
        related_name='evaluations',
    )
    project = models.ForeignKey(
        'projects.HiringProject',
        on_delete=models.CASCADE,
        related_name='evaluations',
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    overall_score = models.FloatField(null=True, blank=True)
    recommendation = models.CharField(
        max_length=20, choices=Recommendation.choices, null=True, blank=True, db_index=True
    )
    candidate_summary = models.TextField(blank=True, default='')
    recruiter_takeaway = models.TextField(blank=True, default='')
    confidence_level = models.CharField(
        max_length=10, choices=ConfidenceLevel.choices, default=ConfidenceLevel.MEDIUM
    )
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    missing_requirements = models.JSONField(default=list)
    red_flags = models.JSONField(default=list)
    notable_projects = models.JSONField(default=list)
    llm_model_used = models.CharField(max_length=100, blank=True, default='')
    prompt_version = models.CharField(max_length=50, default='1.0')
    raw_llm_response = models.JSONField(default=dict)
    evaluation_error = models.TextField(blank=True, default='')
    evaluated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'evaluations_candidate_evaluation'
        verbose_name = 'Candidate Evaluation'
        verbose_name_plural = 'Candidate Evaluations'
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'overall_score']),
            models.Index(fields=['project', 'recommendation']),
            models.Index(fields=['candidate']),
        ]
        ordering = ['-overall_score']

    def __str__(self):
        return f"Evaluation for {self.candidate.name} (score={self.overall_score})"


class CandidateScoreBreakdown(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluation = models.OneToOneField(
        CandidateEvaluation,
        on_delete=models.CASCADE,
        related_name='score_breakdown',
    )
    skills_match_score = models.FloatField(default=0.0)
    experience_depth_score = models.FloatField(default=0.0)
    impact_score = models.FloatField(default=0.0)
    project_relevance_score = models.FloatField(default=0.0)
    communication_resume_quality_score = models.FloatField(default=0.0)
    domain_fit_score = models.FloatField(default=0.0)
    risk_penalty_score = models.FloatField(default=0.0)

    skills_match_reasoning = models.TextField(blank=True, default='')
    experience_depth_reasoning = models.TextField(blank=True, default='')
    impact_reasoning = models.TextField(blank=True, default='')
    project_relevance_reasoning = models.TextField(blank=True, default='')
    communication_reasoning = models.TextField(blank=True, default='')
    domain_fit_reasoning = models.TextField(blank=True, default='')
    risk_reasoning = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'evaluations_score_breakdown'
        verbose_name = 'Score Breakdown'
        verbose_name_plural = 'Score Breakdowns'

    def __str__(self):
        return f"Score breakdown for evaluation {self.evaluation_id}"


class RecruiterQueryHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.HiringProject',
        on_delete=models.CASCADE,
        related_name='recruiter_queries',
    )
    asked_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='recruiter_queries',
    )
    query_text = models.TextField()
    response_text = models.TextField(blank=True, default='')
    candidates_referenced = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'evaluations_recruiter_query'
        verbose_name = 'Recruiter Query'
        verbose_name_plural = 'Recruiter Queries'
        ordering = ['-created_at']

    def __str__(self):
        return f"Query by {self.asked_by} on {self.created_at}"


class CandidateComparison(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.HiringProject',
        on_delete=models.CASCADE,
        related_name='comparisons',
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='comparisons',
    )
    candidate_a = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.CASCADE,
        related_name='comparisons_as_a',
    )
    candidate_b = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.CASCADE,
        related_name='comparisons_as_b',
    )
    comparison_result = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'evaluations_comparison'
        verbose_name = 'Candidate Comparison'
        verbose_name_plural = 'Candidate Comparisons'
        ordering = ['-created_at']

    def __str__(self):
        return f"Comparison: {self.candidate_a.name} vs {self.candidate_b.name}"
