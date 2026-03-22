from rest_framework import serializers
from apps.candidates.models import CandidateResume


class ResumeUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    candidate_id = serializers.UUIDField()

    def validate_file(self, value):
        from django.conf import settings
        max_size = getattr(settings, 'MAX_RESUME_FILE_SIZE', 10 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError(f"File too large. Maximum size is {max_size // (1024*1024)}MB.")

        import os
        _, ext = os.path.splitext(value.name.lower())
        if ext not in ['.pdf', '.docx']:
            raise serializers.ValidationError("Only PDF and DOCX files are supported.")
        return value


class CandidateResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateResume
        fields = [
            'id', 'file_name', 'file_type', 'file_size',
            'parse_status', 'parse_error', 'parsed_at',
            'raw_text', 'created_at',
        ]
        read_only_fields = ['id', 'parse_status', 'parse_error', 'parsed_at', 'created_at']
        extra_kwargs = {
            'raw_text': {'write_only': False},
        }
