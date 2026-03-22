import logging
import os

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.candidates.models import Candidate, CandidateResume
from apps.organizations.models import Membership
from apps.projects.models import HiringProject
from .serializers import ResumeUploadSerializer, CandidateResumeSerializer

logger = logging.getLogger(__name__)


class ResumeUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, project_pk=None, candidate_pk=None):
        try:
            project = HiringProject.objects.get(id=project_pk)
        except HiringProject.DoesNotExist:
            return Response(
                {'data': None, 'message': 'Project not found', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        membership = Membership.objects.filter(
            user=request.user, organization=project.organization, is_active=True
        ).first()
        if not membership:
            return Response(
                {'data': None, 'message': 'Access denied', 'errors': None},
                status=status.HTTP_403_FORBIDDEN
            )

        candidate = get_object_or_404(Candidate, id=candidate_pk, project=project)

        serializer = ResumeUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = serializer.validated_data['file']
        _, ext = os.path.splitext(file.name.lower())
        file_type = CandidateResume.FileType.PDF if ext == '.pdf' else CandidateResume.FileType.DOCX

        # Create or update resume
        resume, created = CandidateResume.objects.update_or_create(
            candidate=candidate,
            defaults={
                'file_path': file,
                'file_name': file.name,
                'file_type': file_type,
                'file_size': file.size,
                'parse_status': CandidateResume.ParseStatus.PENDING,
                'raw_text': '',
                'parse_error': '',
            }
        )

        # Trigger async parsing
        from tasks.resume_tasks import parse_resume_task
        parse_resume_task.delay(str(resume.id))

        return Response(
            {
                'data': CandidateResumeSerializer(resume).data,
                'message': 'Resume uploaded, parsing started',
                'errors': None,
            },
            status=status.HTTP_202_ACCEPTED
        )

    def get(self, request, project_pk=None, candidate_pk=None):
        try:
            project = HiringProject.objects.get(id=project_pk)
        except HiringProject.DoesNotExist:
            return Response(
                {'data': None, 'message': 'Project not found', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        membership = Membership.objects.filter(
            user=request.user, organization=project.organization, is_active=True
        ).first()
        if not membership:
            return Response(
                {'data': None, 'message': 'Access denied', 'errors': None},
                status=status.HTTP_403_FORBIDDEN
            )

        candidate = get_object_or_404(Candidate, id=candidate_pk, project=project)
        try:
            resume = candidate.resume
            return Response(
                {'data': CandidateResumeSerializer(resume).data, 'message': None, 'errors': None}
            )
        except CandidateResume.DoesNotExist:
            return Response(
                {'data': None, 'message': 'No resume found for this candidate', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )


class BulkResumeUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, project_pk=None):
        from django.conf import settings
        max_files = getattr(settings, 'MAX_BULK_RESUME_FILES', 50)

        try:
            project = HiringProject.objects.get(id=project_pk)
        except HiringProject.DoesNotExist:
            return Response(
                {'data': None, 'message': 'Project not found', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        membership = Membership.objects.filter(
            user=request.user, organization=project.organization, is_active=True
        ).first()
        if not membership:
            return Response(
                {'data': None, 'message': 'Access denied', 'errors': None},
                status=status.HTTP_403_FORBIDDEN
            )

        files = request.FILES.getlist('files')
        if not files:
            return Response(
                {'data': None, 'message': 'No files provided', 'errors': {'files': ['At least one file is required.']}},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(files) > max_files:
            return Response(
                {'data': None, 'message': f'Maximum {max_files} files allowed at once', 'errors': None},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        errors = []

        for file in files:
            _, ext = os.path.splitext(file.name.lower())
            if ext not in ['.pdf', '.docx']:
                errors.append({'file': file.name, 'error': 'Only PDF and DOCX files supported'})
                continue

            from django.conf import settings as dj_settings
            max_size = getattr(dj_settings, 'MAX_RESUME_FILE_SIZE', 10 * 1024 * 1024)
            if file.size > max_size:
                errors.append({'file': file.name, 'error': f'File too large (max {max_size // (1024*1024)}MB)'})
                continue

            # Try to match by filename to existing candidate
            name_without_ext = os.path.splitext(file.name)[0]
            candidate = Candidate.objects.filter(
                project=project,
                name__icontains=name_without_ext,
            ).first()

            if not candidate:
                # Create a placeholder candidate
                candidate = Candidate.objects.create(
                    project=project,
                    name=name_without_ext,
                    status=Candidate.Status.PENDING,
                )

            file_type = CandidateResume.FileType.PDF if ext == '.pdf' else CandidateResume.FileType.DOCX
            resume, _ = CandidateResume.objects.update_or_create(
                candidate=candidate,
                defaults={
                    'file_path': file,
                    'file_name': file.name,
                    'file_type': file_type,
                    'file_size': file.size,
                    'parse_status': CandidateResume.ParseStatus.PENDING,
                }
            )

            from tasks.resume_tasks import parse_resume_task
            parse_resume_task.delay(str(resume.id))

            results.append({
                'file': file.name,
                'candidate_id': str(candidate.id),
                'resume_id': str(resume.id),
                'status': 'queued',
            })

        return Response(
            {
                'data': {
                    'processed': results,
                    'errors': errors,
                    'total_queued': len(results),
                    'total_errors': len(errors),
                },
                'message': f'{len(results)} resumes queued for processing',
                'errors': None,
            },
            status=status.HTTP_202_ACCEPTED
        )
