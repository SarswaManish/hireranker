import logging

from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from apps.candidates.views import get_project_membership
from .services import export_rankings_to_csv, export_candidates_to_csv
from core.utils import log_event, AuditEventType

logger = logging.getLogger(__name__)


class ExportRankingsCSVView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_pk=None):
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            csv_content = export_rankings_to_csv(project)
        except Exception as e:
            logger.error("CSV export failed for project %s: %s", project_pk, e)
            return Response(
                {'data': None, 'message': f'Export failed: {str(e)}', 'errors': None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"rankings_{project.name}_{timestamp}.csv".replace(' ', '_')

        log_event(request.user, AuditEventType.EXPORT_DOWNLOADED, {
            'project_id': str(project.id),
            'export_type': 'rankings_csv',
        })

        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['X-Total-Count'] = str(csv_content.count(b'\n') - 1)
        return response


class ExportCandidatesCSVView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_pk=None):
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        include_unevaluated = request.query_params.get('include_unevaluated', 'false').lower() == 'true'

        try:
            csv_content = export_candidates_to_csv(project, include_unevaluated=include_unevaluated)
        except Exception as e:
            logger.error("Candidates CSV export failed for project %s: %s", project_pk, e)
            return Response(
                {'data': None, 'message': f'Export failed: {str(e)}', 'errors': None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"candidates_{project.name}_{timestamp}.csv".replace(' ', '_')

        log_event(request.user, AuditEventType.EXPORT_DOWNLOADED, {
            'project_id': str(project.id),
            'export_type': 'candidates_csv',
        })

        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
