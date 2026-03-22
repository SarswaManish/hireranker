from django.contrib import admin

from .models import (
    CandidateEvaluation,
    CandidateScoreBreakdown,
    RecruiterQueryHistory,
    CandidateComparison,
)


@admin.register(CandidateEvaluation)
class CandidateEvaluationAdmin(admin.ModelAdmin):
    list_display = [
        'candidate', 'project', 'status', 'overall_score',
        'recommendation', 'confidence_level', 'evaluated_at',
    ]
    list_filter = ['status', 'recommendation', 'confidence_level', 'evaluated_at']
    search_fields = ['candidate__name', 'candidate__email', 'project__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'evaluated_at']
    raw_id_fields = ['candidate', 'project']
    list_select_related = ['candidate', 'project']


@admin.register(CandidateScoreBreakdown)
class CandidateScoreBreakdownAdmin(admin.ModelAdmin):
    list_display = [
        'evaluation', 'skills_match_score', 'experience_depth_score',
        'impact_score', 'domain_fit_score',
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['evaluation']


@admin.register(RecruiterQueryHistory)
class RecruiterQueryHistoryAdmin(admin.ModelAdmin):
    list_display = ['project', 'asked_by', 'query_text', 'created_at']
    list_filter = ['created_at']
    search_fields = ['query_text', 'project__name']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['project', 'asked_by']


@admin.register(CandidateComparison)
class CandidateComparisonAdmin(admin.ModelAdmin):
    list_display = ['project', 'candidate_a', 'candidate_b', 'created_by', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['project', 'created_by', 'candidate_a', 'candidate_b']
