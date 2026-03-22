from rest_framework import serializers

from .models import (
    CandidateEvaluation,
    CandidateScoreBreakdown,
    RecruiterQueryHistory,
    CandidateComparison,
)


class ScoreBreakdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateScoreBreakdown
        fields = [
            'skills_match_score', 'experience_depth_score', 'impact_score',
            'project_relevance_score', 'communication_resume_quality_score',
            'domain_fit_score', 'risk_penalty_score',
            'skills_match_reasoning', 'experience_depth_reasoning',
            'impact_reasoning', 'project_relevance_reasoning',
            'communication_reasoning', 'domain_fit_reasoning', 'risk_reasoning',
        ]


class CandidateEvaluationSerializer(serializers.ModelSerializer):
    score_breakdown = ScoreBreakdownSerializer(read_only=True)

    class Meta:
        model = CandidateEvaluation
        fields = [
            'id', 'candidate', 'project', 'status', 'overall_score',
            'recommendation', 'candidate_summary', 'recruiter_takeaway',
            'confidence_level', 'strengths', 'weaknesses',
            'missing_requirements', 'red_flags', 'notable_projects',
            'llm_model_used', 'prompt_version', 'evaluation_error',
            'evaluated_at', 'created_at', 'updated_at',
            'score_breakdown',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RankedCandidateSerializer(serializers.Serializer):
    """Serializer for ranked candidate list."""
    id = serializers.UUIDField()
    name = serializers.CharField()
    email = serializers.CharField()
    location = serializers.CharField()
    college = serializers.CharField()
    skills = serializers.ListField(child=serializers.CharField())
    overall_score = serializers.FloatField(allow_null=True)
    recommendation = serializers.CharField(allow_null=True)
    candidate_summary = serializers.CharField(allow_null=True)
    recruiter_takeaway = serializers.CharField(allow_null=True)
    confidence_level = serializers.CharField(allow_null=True)
    strengths = serializers.ListField(allow_null=True)
    weaknesses = serializers.ListField(allow_null=True)
    missing_requirements = serializers.ListField(allow_null=True)
    red_flags = serializers.ListField(allow_null=True)
    rank = serializers.IntegerField()


class RecruiterQueryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruiterQueryHistory
        fields = ['id', 'project', 'asked_by', 'query_text', 'response_text', 'candidates_referenced', 'created_at']
        read_only_fields = ['id', 'asked_by', 'created_at']


class CandidateComparisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateComparison
        fields = ['id', 'project', 'created_by', 'candidate_a', 'candidate_b', 'comparison_result', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']


class TriggerEvaluationSerializer(serializers.Serializer):
    candidate_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text='Optional list of specific candidate IDs to evaluate. Evaluates all if omitted.',
    )


class CompareCandidatesSerializer(serializers.Serializer):
    candidate_a_id = serializers.UUIDField()
    candidate_b_id = serializers.UUIDField()

    def validate(self, attrs):
        if attrs['candidate_a_id'] == attrs['candidate_b_id']:
            raise serializers.ValidationError("Cannot compare a candidate with itself.")
        return attrs
