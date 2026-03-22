from rest_framework import serializers

from .models import HiringProject, JobDescriptionSnapshot
from apps.accounts.serializers import UserSerializer


class JobDescriptionSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDescriptionSnapshot
        fields = ['id', 'raw_text', 'structured_requirements', 'parsed_at', 'parser_version', 'created_at']
        read_only_fields = ['id', 'parsed_at', 'created_at']


class HiringProjectSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    candidate_count = serializers.SerializerMethodField()
    evaluated_count = serializers.SerializerMethodField()
    latest_jd_snapshot = serializers.SerializerMethodField()

    class Meta:
        model = HiringProject
        fields = [
            'id', 'organization', 'name', 'company_name', 'role_title',
            'job_description', 'must_have_skills', 'good_to_have_skills',
            'min_experience_years', 'location_preference', 'degree_requirement',
            'notice_period_days', 'status', 'created_by', 'created_at', 'updated_at',
            'candidate_count', 'evaluated_count', 'latest_jd_snapshot',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_candidate_count(self, obj):
        return obj.candidates.filter(is_duplicate=False).count()

    def get_evaluated_count(self, obj):
        return obj.candidates.filter(
            is_duplicate=False,
            evaluations__status='completed'
        ).distinct().count()

    def get_latest_jd_snapshot(self, obj):
        snapshot = obj.jd_snapshots.first()
        if snapshot:
            return JobDescriptionSnapshotSerializer(snapshot).data
        return None


class HiringProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HiringProject
        fields = [
            'name', 'company_name', 'role_title', 'job_description',
            'must_have_skills', 'good_to_have_skills', 'min_experience_years',
            'location_preference', 'degree_requirement', 'notice_period_days', 'status',
        ]

    def validate_must_have_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list.")
        return value

    def validate_good_to_have_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list.")
        return value


class ProjectStatsSerializer(serializers.Serializer):
    total_candidates = serializers.IntegerField()
    evaluated_candidates = serializers.IntegerField()
    pending_evaluation = serializers.IntegerField()
    strong_yes_count = serializers.IntegerField()
    yes_count = serializers.IntegerField()
    maybe_count = serializers.IntegerField()
    no_count = serializers.IntegerField()
    average_score = serializers.FloatField(allow_null=True)
    top_score = serializers.FloatField(allow_null=True)
