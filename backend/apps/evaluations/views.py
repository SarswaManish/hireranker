import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CandidateEvaluation, CandidateComparison
from .serializers import (
    CandidateEvaluationSerializer,
    RankedCandidateSerializer,
    CandidateComparisonSerializer,
    TriggerEvaluationSerializer,
    CompareCandidatesSerializer,
)
from apps.candidates.models import Candidate
from apps.candidates.views import get_project_membership
from apps.organizations.models import Membership
from apps.projects.models import HiringProject
from core.pagination import StandardResultsSetPagination
from core.utils import log_event, AuditEventType

logger = logging.getLogger(__name__)


class ProjectRankingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_pk=None):
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get evaluated candidates ordered by score
        evaluations = CandidateEvaluation.objects.filter(
            project=project,
            status=CandidateEvaluation.Status.COMPLETED,
            candidate__is_duplicate=False,
        ).select_related(
            'candidate', 'score_breakdown'
        ).order_by('-overall_score')

        # Apply optional recommendation filter
        rec_filter = request.query_params.get('recommendation')
        if rec_filter:
            evaluations = evaluations.filter(recommendation=rec_filter)

        score_min = request.query_params.get('score_min')
        if score_min:
            try:
                evaluations = evaluations.filter(overall_score__gte=float(score_min))
            except ValueError:
                pass

        score_max = request.query_params.get('score_max')
        if score_max:
            try:
                evaluations = evaluations.filter(overall_score__lte=float(score_max))
            except ValueError:
                pass

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(evaluations, request)

        result_data = []
        start_rank = paginator.page.start_index() if hasattr(paginator, 'page') and paginator.page else 1

        for rank_offset, evaluation in enumerate(page if page is not None else evaluations):
            candidate = evaluation.candidate
            result_data.append({
                'id': str(candidate.id),
                'name': candidate.name,
                'email': candidate.email,
                'location': candidate.location,
                'college': candidate.college,
                'skills': candidate.skills,
                'overall_score': evaluation.overall_score,
                'recommendation': evaluation.recommendation,
                'candidate_summary': evaluation.candidate_summary,
                'recruiter_takeaway': evaluation.recruiter_takeaway,
                'confidence_level': evaluation.confidence_level,
                'strengths': evaluation.strengths,
                'weaknesses': evaluation.weaknesses,
                'missing_requirements': evaluation.missing_requirements,
                'red_flags': evaluation.red_flags,
                'rank': start_rank + rank_offset,
            })

        if page is not None:
            return paginator.get_paginated_response(result_data)
        return Response({'data': result_data, 'message': None, 'errors': None})


class TriggerEvaluationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_pk=None):
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TriggerEvaluationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        candidate_ids = serializer.validated_data.get('candidate_ids')

        if candidate_ids:
            # Evaluate specific candidates
            from tasks.evaluation_tasks import evaluate_candidate_task
            count = 0
            for cid in candidate_ids:
                candidate = Candidate.objects.filter(id=cid, project=project).first()
                if candidate:
                    evaluate_candidate_task.delay(str(cid))
                    count += 1
        else:
            # Evaluate all eligible
            from apps.evaluations.services import batch_evaluate_project
            count = batch_evaluate_project(project)

        log_event(request.user, AuditEventType.EVALUATION_STARTED, {
            'project_id': str(project.id),
            'triggered_count': count,
        })

        return Response(
            {
                'data': {'triggered_count': count},
                'message': f'{count} evaluations triggered',
                'errors': None,
            },
            status=status.HTTP_202_ACCEPTED
        )

    def get(self, request, project_pk=None):
        """Get evaluation batch status."""
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        total = Candidate.objects.filter(project=project, is_duplicate=False).count()
        pending = CandidateEvaluation.objects.filter(
            project=project, status__in=['pending', 'running']
        ).count()
        completed = CandidateEvaluation.objects.filter(project=project, status='completed').count()
        failed = CandidateEvaluation.objects.filter(project=project, status='failed').count()

        return Response({
            'data': {
                'total_candidates': total,
                'pending': pending,
                'completed': completed,
                'failed': failed,
                'progress_pct': round((completed / total * 100) if total > 0 else 0, 1),
            },
            'message': None,
            'errors': None,
        })


class CandidateEvaluationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_pk=None, candidate_pk=None):
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        candidate = get_object_or_404(Candidate, id=candidate_pk, project=project)
        evaluation = CandidateEvaluation.objects.filter(
            candidate=candidate,
            status=CandidateEvaluation.Status.COMPLETED,
        ).select_related('score_breakdown').first()

        if not evaluation:
            # Also check for pending/running
            evaluation = CandidateEvaluation.objects.filter(
                candidate=candidate
            ).select_related('score_breakdown').first()

        if not evaluation:
            return Response(
                {'data': None, 'message': 'No evaluation found for this candidate', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {'data': CandidateEvaluationSerializer(evaluation).data, 'message': None, 'errors': None}
        )


class CompareCandidatesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_pk=None):
        project, membership = get_project_membership(request.user, project_pk)
        if not project or not membership:
            return Response(
                {'data': None, 'message': 'Project not found or access denied', 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CompareCandidatesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        candidate_a = get_object_or_404(Candidate, id=serializer.validated_data['candidate_a_id'], project=project)
        candidate_b = get_object_or_404(Candidate, id=serializer.validated_data['candidate_b_id'], project=project)

        # Check both have evaluations
        eval_a = CandidateEvaluation.objects.filter(candidate=candidate_a, status='completed').first()
        eval_b = CandidateEvaluation.objects.filter(candidate=candidate_b, status='completed').first()

        if not eval_a or not eval_b:
            return Response(
                {
                    'data': None,
                    'message': 'Both candidates must have completed evaluations before comparison',
                    'errors': None,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Run LLM comparison
        try:
            from core.llm.client import get_llm_client
            from core.llm.prompts import CompareCandidatesPrompt

            client = get_llm_client()
            prompt = CompareCandidatesPrompt()

            comparison_data = {
                'candidate_a': {
                    'name': candidate_a.name,
                    'score': eval_a.overall_score,
                    'recommendation': eval_a.recommendation,
                    'summary': eval_a.candidate_summary,
                    'strengths': eval_a.strengths,
                    'weaknesses': eval_a.weaknesses,
                    'skills': candidate_a.skills,
                },
                'candidate_b': {
                    'name': candidate_b.name,
                    'score': eval_b.overall_score,
                    'recommendation': eval_b.recommendation,
                    'summary': eval_b.candidate_summary,
                    'strengths': eval_b.strengths,
                    'weaknesses': eval_b.weaknesses,
                    'skills': candidate_b.skills,
                },
                'role_title': project.role_title,
            }

            messages = [
                {'role': 'system', 'content': prompt.system_prompt()},
                {'role': 'user', 'content': prompt.user_prompt(comparison_data)},
            ]

            response = client.complete_with_retry(
                messages=messages,
                temperature=0.2,
                max_tokens=2000,
                response_format={'type': 'json_object'},
            )

            comparison_result = client.parse_json_response(response)

            comparison = CandidateComparison.objects.create(
                project=project,
                created_by=request.user,
                candidate_a=candidate_a,
                candidate_b=candidate_b,
                comparison_result=comparison_result,
            )

            return Response(
                {
                    'data': CandidateComparisonSerializer(comparison).data,
                    'message': 'Comparison completed',
                    'errors': None,
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error("Comparison failed: %s", e)
            return Response(
                {'data': None, 'message': f'Comparison failed: {str(e)}', 'errors': None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
