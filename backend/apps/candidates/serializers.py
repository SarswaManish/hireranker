from rest_framework import serializers

from .models import Candidate, CandidateImportBatch, CandidateResume, CandidateTag


class CandidateTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateTag
        fields = ['id', 'tag', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']


class CandidateResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateResume
        fields = [
            'id', 'file_name', 'file_type', 'file_size',
            'parse_status', 'parse_error', 'parsed_at', 'created_at',
        ]
        read_only_fields = ['id', 'parse_status', 'parse_error', 'parsed_at', 'created_at']


class CandidateListSerializer(serializers.ModelSerializer):
    tags = CandidateTagSerializer(many=True, read_only=True)
    overall_score = serializers.SerializerMethodField()
    recommendation = serializers.SerializerMethodField()
    resume_parse_status = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = [
            'id', 'name', 'email', 'phone', 'location', 'college', 'degree',
            'graduation_year', 'cgpa', 'skills', 'github_url', 'linkedin_url',
            'portfolio_url', 'resume_url', 'status', 'is_duplicate',
            'tags', 'overall_score', 'recommendation', 'resume_parse_status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'is_duplicate', 'created_at', 'updated_at']

    def get_overall_score(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'evaluations' in obj._prefetched_objects_cache:
            evals = obj._prefetched_objects_cache['evaluations']
            completed = [e for e in evals if e.status == 'completed']
            if completed:
                return completed[0].overall_score
        try:
            evaluation = obj.evaluations.filter(status='completed').first()
            return evaluation.overall_score if evaluation else None
        except Exception:
            return None

    def get_recommendation(self, obj):
        try:
            evaluation = obj.evaluations.filter(status='completed').first()
            return evaluation.recommendation if evaluation else None
        except Exception:
            return None

    def get_resume_parse_status(self, obj):
        try:
            return obj.resume.parse_status
        except Exception:
            return None


class CandidateDetailSerializer(serializers.ModelSerializer):
    tags = CandidateTagSerializer(many=True, read_only=True)
    resume = CandidateResumeSerializer(read_only=True)
    evaluation = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = [
            'id', 'project', 'batch', 'name', 'email', 'phone', 'location',
            'college', 'degree', 'graduation_year', 'cgpa', 'skills',
            'github_url', 'linkedin_url', 'portfolio_url', 'resume_url',
            'notes', 'status', 'is_duplicate', 'duplicate_of',
            'tags', 'resume', 'evaluation', 'raw_data',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'project', 'batch', 'status', 'is_duplicate', 'duplicate_of',
            'raw_data', 'created_at', 'updated_at',
        ]

    def get_evaluation(self, obj):
        try:
            evaluation = obj.evaluations.filter(status='completed').first()
            if evaluation:
                from apps.evaluations.serializers import CandidateEvaluationSerializer
                return CandidateEvaluationSerializer(evaluation).data
            return None
        except Exception:
            return None


class CandidateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = [
            'name', 'email', 'phone', 'location', 'college', 'degree',
            'graduation_year', 'cgpa', 'skills', 'github_url', 'linkedin_url',
            'portfolio_url', 'resume_url', 'notes',
        ]


class CandidateImportBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateImportBatch
        fields = [
            'id', 'project', 'imported_by', 'file_name', 'total_rows',
            'processed_rows', 'failed_rows', 'status', 'column_mapping',
            'error_log', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'imported_by', 'total_rows', 'processed_rows', 'failed_rows',
            'status', 'error_log', 'created_at', 'updated_at',
        ]


class ColumnSuggestionSerializer(serializers.Serializer):
    columns = serializers.ListField(child=serializers.CharField())
    suggestions = serializers.DictField(child=serializers.CharField(allow_blank=True))


class AddTagSerializer(serializers.Serializer):
    tag = serializers.CharField(max_length=100)

    def validate_tag(self, value):
        return value.strip().lower()


class RecruiterQuerySerializer(serializers.Serializer):
    query = serializers.CharField(min_length=5, max_length=2000)
