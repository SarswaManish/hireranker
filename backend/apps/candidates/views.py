import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Candidate, CandidateImportBatch, CandidateTag
from .serializers import (
    CandidateListSerializer,
    CandidateDetailSerializer,
    CandidateUpdateSerializer,
    CandidateImportBatchSerializer,
    ColumnSuggestionSerializer,
    AddTagSerializer,
    RecruiterQuerySerializer,
)
from .importers import validate_file, detect_columns, import_candidates_from_file, detect_duplicates
from apps.projects.models import HiringProject
from apps.organizations.models import Membership
from core.pagination import StandardResultsSetPagination
from core.utils import log_event, AuditEventType

logger = logging.getLogger(__name__)


def get_project_membership(user, project_id):
    """Helper: get project and verify user has membership."""
    try:
        project = HiringProject.objects.select_related('organization').get(id=project_id)
    except HiringProject.DoesNotExist:
        return None, None
    membership = Membership.objects.filter(
        user=user,
        organization=project.organization,
        is_active=True,
    ).first()
    return project, membership


class CandidateImportBatchViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def create(self, request, project_pk=None):
        """POST /api/projects/{project_id}/import/"""
        project, membership = get_project_membership(request.user, project_pk)
        if not project:
            return Response(
                {'data': None, 'message': 'Project not found', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )
        if not membership:
            return Response(
                {'data': None, 'message': 'Access denied', 'errors': None},
                status=status.HTTP_403_FORBIDDEN
            )

        file = request.FILES.get('file')
        if not file:
            return Response(
                {'data': None, 'message': 'File is required', 'errors': {'file': ['This field is required.']}},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_valid, error_msg = validate_file(file)
        if not is_valid:
            return Response(
                {'data': None, 'message': error_msg, 'errors': {'file': [error_msg]}},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get optional column mapping from request
        column_mapping = {}
        if 'column_mapping' in request.data:
            try:
                import json
                column_mapping = json.loads(request.data['column_mapping'])
            except (ValueError, TypeError):
                pass

        # Create batch record
        batch = CandidateImportBatch.objects.create(
            project=project,
            imported_by=request.user,
            file_name=file.name,
            file_path=file,
            status=CandidateImportBatch.Status.PENDING,
        )

        # Trigger async processing
        from tasks.resume_tasks import process_candidate_batch
        process_candidate_batch.delay(str(batch.id), column_mapping=column_mapping)

        log_event(request.user, AuditEventType.FILE_UPLOADED, {
            'batch_id': str(batch.id),
            'file_name': file.name,
            'project_id': str(project.id),
        })

        return Response(
            {'data': CandidateImportBatchSerializer(batch).data, 'message': 'Import started', 'errors': None},
            status=status.HTTP_202_ACCEPTED
        )

    def retrieve(self, request, project_pk=None, pk=None):
        """GET /api/projects/{project_id}/import/{batch_id}/status/"""
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )
        batch = get_object_or_404(CandidateImportBatch, id=pk, project=project)
        return Response(
            {'data': CandidateImportBatchSerializer(batch).data, 'message': None, 'errors': None}
        )

    def list(self, request, project_pk=None):
        """GET /api/projects/{project_id}/import/"""
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )
        batches = CandidateImportBatch.objects.filter(project=project).order_by('-created_at')
        return Response(
            {'data': CandidateImportBatchSerializer(batches, many=True).data, 'message': None, 'errors': None}
        )


class CandidateViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, project):
        return Candidate.objects.filter(
            project=project,
            is_duplicate=False,
        ).select_related('batch').prefetch_related('tags', 'evaluations').order_by('-created_at')

    def apply_filters(self, qs, request):
        """Apply search and filter params."""
        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(skills__icontains=search) |
                Q(college__icontains=search)
            )

        recommendation = request.query_params.get('recommendation')
        if recommendation:
            qs = qs.filter(evaluations__recommendation=recommendation, evaluations__status='completed')

        eval_status = request.query_params.get('status')
        if eval_status:
            qs = qs.filter(status=eval_status)

        score_min = request.query_params.get('score_min')
        if score_min:
            try:
                qs = qs.filter(evaluations__overall_score__gte=float(score_min), evaluations__status='completed')
            except ValueError:
                pass

        score_max = request.query_params.get('score_max')
        if score_max:
            try:
                qs = qs.filter(evaluations__overall_score__lte=float(score_max), evaluations__status='completed')
            except ValueError:
                pass

        # Sorting
        sort_by = request.query_params.get('sort_by', '-created_at')
        allowed_sorts = {
            'score': '-evaluations__overall_score',
            '-score': 'evaluations__overall_score',
            'name': 'name',
            '-name': '-name',
            'created_at': 'created_at',
            '-created_at': '-created_at',
        }
        if sort_by in allowed_sorts:
            qs = qs.order_by(allowed_sorts[sort_by])

        return qs.distinct()

    def list(self, request, project_pk=None):
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )
        qs = self.apply_filters(self.get_queryset(project), request)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = CandidateListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = CandidateListSerializer(qs, many=True)
        return Response({'data': serializer.data, 'message': None, 'errors': None})

    def retrieve(self, request, project_pk=None, pk=None):
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )
        candidate = get_object_or_404(Candidate, id=pk, project=project)
        return Response(
            {'data': CandidateDetailSerializer(candidate).data, 'message': None, 'errors': None}
        )

    def partial_update(self, request, project_pk=None, pk=None):
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )
        candidate = get_object_or_404(Candidate, id=pk, project=project)
        serializer = CandidateUpdateSerializer(candidate, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response(
            {'data': CandidateDetailSerializer(candidate).data, 'message': 'Candidate updated', 'errors': None}
        )

    @action(detail=True, methods=['post'], url_path='add_tag')
    def add_tag(self, request, project_pk=None, pk=None):
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )
        candidate = get_object_or_404(Candidate, id=pk, project=project)
        serializer = AddTagSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        tag, created = CandidateTag.objects.get_or_create(
            candidate=candidate,
            tag=serializer.validated_data['tag'],
            defaults={'created_by': request.user}
        )
        from .serializers import CandidateTagSerializer
        return Response(
            {'data': CandidateTagSerializer(tag).data, 'message': 'Tag added', 'errors': None},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    @action(detail=True, methods=['delete'], url_path='tags/(?P<tag_id>[^/.]+)')
    def remove_tag(self, request, project_pk=None, pk=None, tag_id=None):
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )
        candidate = get_object_or_404(Candidate, id=pk, project=project)
        tag = get_object_or_404(CandidateTag, id=tag_id, candidate=candidate)
        tag.delete()
        return Response(
            {'data': None, 'message': 'Tag removed', 'errors': None},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='column_suggestions')
    def column_suggestions(self, request, project_pk=None):
        """
        For a given file, return column auto-detection suggestions.
        POST with 'file' to get suggestions.
        """
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        file = request.FILES.get('file')
        if not file:
            # Return the field name aliases as reference
            from .importers import COLUMN_ALIASES
            return Response({
                'data': {
                    'fields': list(COLUMN_ALIASES.keys()),
                    'aliases': {k: v[:5] for k, v in COLUMN_ALIASES.items()},
                },
                'message': 'Upload a file to get column suggestions',
                'errors': None,
            })

        try:
            import pandas as pd
            if file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file, nrows=0, dtype=str)
            else:
                df = pd.read_csv(file, nrows=0, dtype=str)

            suggestions = detect_columns(df)
            return Response({
                'data': {
                    'columns': list(df.columns),
                    'suggestions': suggestions,
                },
                'message': None,
                'errors': None,
            })
        except Exception as e:
            return Response(
                {'data': None, 'message': f'Failed to read file: {str(e)}', 'errors': None},
                status=status.HTTP_400_BAD_REQUEST
            )


class RecruiterQueryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_pk=None):
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = RecruiterQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.evaluations.models import RecruiterQueryHistory
        query_text = serializer.validated_data['query']

        # Create query record
        query_history = RecruiterQueryHistory.objects.create(
            project=project,
            asked_by=request.user,
            query_text=query_text,
            response_text='',
            candidates_referenced=[],
        )

        log_event(request.user, AuditEventType.QUERY_ASKED, {
            'project_id': str(project.id),
            'query_id': str(query_history.id),
        })

        # Trigger async task
        from tasks.evaluation_tasks import answer_recruiter_query_task
        answer_recruiter_query_task.delay(str(query_history.id))

        return Response(
            {
                'data': {
                    'query_id': str(query_history.id),
                    'status': 'processing',
                    'message': 'Your query is being processed',
                },
                'message': 'Query submitted',
                'errors': None,
            },
            status=status.HTTP_202_ACCEPTED
        )

    def get(self, request, project_pk=None):
        """Poll for query result."""
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        query_id = request.query_params.get('query_id')
        if not query_id:
            # Return last 10 queries for this project
            from apps.evaluations.models import RecruiterQueryHistory
            queries = RecruiterQueryHistory.objects.filter(
                project=project
            ).order_by('-created_at')[:10]
            from apps.evaluations.serializers import RecruiterQueryHistorySerializer
            return Response({'data': RecruiterQueryHistorySerializer(queries, many=True).data, 'message': None, 'errors': None})

        from apps.evaluations.models import RecruiterQueryHistory
        query = get_object_or_404(RecruiterQueryHistory, id=query_id, project=project)
        from apps.evaluations.serializers import RecruiterQueryHistorySerializer
        return Response({'data': RecruiterQueryHistorySerializer(query).data, 'message': None, 'errors': None})
