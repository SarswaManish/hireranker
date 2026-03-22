import logging

from django.db.models import Avg, Max
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import HiringProject, JobDescriptionSnapshot
from .serializers import (
    HiringProjectSerializer,
    HiringProjectCreateSerializer,
    JobDescriptionSnapshotSerializer,
    ProjectStatsSerializer,
)
from apps.organizations.models import Membership, Organization
from core.permissions import get_user_org_membership
from core.utils import log_event, AuditEventType

logger = logging.getLogger(__name__)


def get_project_or_403(user, project_id):
    """Get a project and check the user belongs to the organization."""
    project = get_object_or_404(HiringProject, id=project_id)
    membership = Membership.objects.filter(
        user=user,
        organization=project.organization,
        is_active=True,
    ).first()
    if not membership:
        return None, None
    return project, membership


class HiringProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = HiringProjectSerializer

    def get_queryset(self):
        user = self.request.user
        org_id = self.request.query_params.get('organization')
        qs = HiringProject.objects.filter(
            organization__memberships__user=user,
            organization__memberships__is_active=True,
        ).select_related('created_by', 'organization').distinct()

        if org_id:
            qs = qs.filter(organization_id=org_id)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        org_id = request.data.get('organization')
        if not org_id:
            return Response(
                {'data': None, 'message': 'organization is required', 'errors': {'organization': ['This field is required.']}},
                status=status.HTTP_400_BAD_REQUEST
            )
        org = get_object_or_404(Organization, id=org_id, is_active=True)
        membership = Membership.objects.filter(user=request.user, organization=org, is_active=True).first()
        if not membership:
            return Response(
                {'data': None, 'message': 'You are not a member of this organization', 'errors': None},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = HiringProjectCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        project = serializer.save(organization=org, created_by=request.user)
        log_event(request.user, AuditEventType.PROJECT_CREATED, {'project_id': str(project.id), 'org_id': str(org.id)})
        return Response(
            {'data': HiringProjectSerializer(project).data, 'message': 'Project created', 'errors': None},
            status=status.HTTP_201_CREATED
        )

    def retrieve(self, request, *args, **kwargs):
        project, membership = get_project_or_403(request.user, kwargs['pk'])
        if not project:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(
            {'data': HiringProjectSerializer(project).data, 'message': None, 'errors': None}
        )

    def partial_update(self, request, *args, **kwargs):
        project, membership = get_project_or_403(request.user, kwargs['pk'])
        if not project:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = HiringProjectCreateSerializer(project, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        project = serializer.save()
        return Response(
            {'data': HiringProjectSerializer(project).data, 'message': 'Project updated', 'errors': None}
        )

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        project, membership = get_project_or_403(request.user, kwargs['pk'])
        if not project:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )
        if membership.role not in [Membership.Role.OWNER, Membership.Role.ADMIN]:
            return Response(
                {'data': None, 'message': 'Permission denied', 'errors': None},
                status=status.HTTP_403_FORBIDDEN
            )
        project.status = HiringProject.Status.ARCHIVED
        project.save()
        return Response(
            {'data': None, 'message': 'Project archived', 'errors': None},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def parse_jd(self, request, pk=None):
        project, membership = get_project_or_403(request.user, pk)
        if not project:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        from apps.evaluations.services import parse_jd_requirements
        try:
            snapshot = parse_jd_requirements(project)
            return Response(
                {'data': JobDescriptionSnapshotSerializer(snapshot).data, 'message': 'JD parsed successfully', 'errors': None},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error("Failed to parse JD for project %s: %s", pk, e)
            return Response(
                {'data': None, 'message': f'Failed to parse JD: {str(e)}', 'errors': None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        project, membership = get_project_or_403(request.user, pk)
        if not project:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        from apps.candidates.models import Candidate
        from apps.evaluations.models import CandidateEvaluation

        candidates = Candidate.objects.filter(project=project, is_duplicate=False)
        evaluations = CandidateEvaluation.objects.filter(project=project, status='completed')

        rec_counts = {}
        for rec in ['strong_yes', 'yes', 'maybe', 'no']:
            rec_counts[rec] = evaluations.filter(recommendation=rec).count()

        agg = evaluations.aggregate(avg=Avg('overall_score'), top=Max('overall_score'))

        stats = {
            'total_candidates': candidates.count(),
            'evaluated_candidates': evaluations.count(),
            'pending_evaluation': candidates.filter(status__in=['pending', 'evaluating']).count(),
            'strong_yes_count': rec_counts.get('strong_yes', 0),
            'yes_count': rec_counts.get('yes', 0),
            'maybe_count': rec_counts.get('maybe', 0),
            'no_count': rec_counts.get('no', 0),
            'average_score': agg['avg'],
            'top_score': agg['top'],
        }

        return Response({'data': stats, 'message': None, 'errors': None})
