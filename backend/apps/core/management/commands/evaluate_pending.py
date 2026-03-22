"""
Management command to re-trigger evaluation for pending candidates.
Useful for recovering from evaluation failures or re-running evaluations.
"""
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Re-trigger evaluation for pending/failed candidates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=str,
            help='Evaluate only candidates in this project ID',
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['pending', 'failed', 'all'],
            default='pending',
            help='Which candidates to evaluate (default: pending)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually triggering evaluations',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of candidates to evaluate (default: 100)',
        )

    def handle(self, *args, **options):
        from apps.candidates.models import Candidate
        from apps.evaluations.models import CandidateEvaluation
        from tasks.evaluation_tasks import evaluate_candidate_task

        project_id = options.get('project_id')
        status_filter = options['status']
        dry_run = options['dry_run']
        limit = options['limit']

        # Build queryset
        qs = Candidate.objects.filter(is_duplicate=False).select_related('project')

        if project_id:
            qs = qs.filter(project_id=project_id)

        if status_filter == 'pending':
            qs = qs.filter(status__in=['pending', 'parsed'])
        elif status_filter == 'failed':
            qs = qs.filter(status='failed')
        elif status_filter == 'all':
            qs = qs.exclude(status='completed')

        # Also include candidates with failed evaluations
        if status_filter in ['failed', 'all']:
            failed_eval_candidate_ids = CandidateEvaluation.objects.filter(
                status='failed'
            ).values_list('candidate_id', flat=True)
            from django.db.models import Q
            qs = qs.filter(
                Q(status__in=['pending', 'parsed', 'failed']) |
                Q(id__in=failed_eval_candidate_ids)
            )

        qs = qs[:limit]
        count = qs.count()

        if count == 0:
            self.stdout.write(self.style.WARNING('No candidates found to evaluate.'))
            return

        self.stdout.write(
            f'Found {count} candidate(s) to evaluate'
            + (' [DRY RUN]' if dry_run else '')
        )

        if dry_run:
            for candidate in qs:
                self.stdout.write(
                    f'  Would evaluate: {candidate.name} ({candidate.email}) '
                    f'in project: {candidate.project.name}'
                )
            return

        triggered = 0
        for candidate in qs:
            try:
                evaluate_candidate_task.delay(str(candidate.id))
                triggered += 1
                self.stdout.write(
                    f'  Queued: {candidate.name} ({candidate.id})'
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  Failed to queue {candidate.name}: {e}')
                )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'Successfully triggered {triggered} evaluation(s).')
        )
