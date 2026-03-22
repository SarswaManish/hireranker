import uuid

from django.db import models
from django.utils import timezone


class CandidateImportBatch(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.HiringProject',
        on_delete=models.CASCADE,
        related_name='import_batches',
    )
    imported_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='import_batches',
    )
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='imports/', max_length=500)
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    column_mapping = models.JSONField(default=dict)
    error_log = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidates_import_batch'
        verbose_name = 'Import Batch'
        verbose_name_plural = 'Import Batches'
        ordering = ['-created_at']

    def __str__(self):
        return f"Batch {self.file_name} ({self.status})"


class Candidate(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PARSING = 'parsing', 'Parsing'
        PARSED = 'parsed', 'Parsed'
        EVALUATING = 'evaluating', 'Evaluating'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.HiringProject',
        on_delete=models.CASCADE,
        related_name='candidates',
        db_index=True,
    )
    batch = models.ForeignKey(
        CandidateImportBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidates',
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=50, blank=True, default='')
    location = models.CharField(max_length=255, blank=True, default='')
    college = models.CharField(max_length=255, blank=True, default='')
    degree = models.CharField(max_length=255, blank=True, default='')
    graduation_year = models.IntegerField(null=True, blank=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    skills = models.JSONField(default=list)
    github_url = models.URLField(blank=True, default='')
    linkedin_url = models.URLField(blank=True, default='')
    portfolio_url = models.URLField(blank=True, default='')
    resume_url = models.URLField(blank=True, default='', max_length=1000)
    notes = models.TextField(blank=True, default='')
    raw_data = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    duplicate_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='duplicates',
    )
    is_duplicate = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidates_candidate'
        verbose_name = 'Candidate'
        verbose_name_plural = 'Candidates'
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'is_duplicate']),
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.email})"


class CandidateResume(models.Model):
    class FileType(models.TextChoices):
        PDF = 'pdf', 'PDF'
        DOCX = 'docx', 'DOCX'
        URL = 'url', 'URL'

    class ParseStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PARSING = 'parsing', 'Parsing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.OneToOneField(
        Candidate,
        on_delete=models.CASCADE,
        related_name='resume',
    )
    file_path = models.FileField(upload_to='resumes/', max_length=500, blank=True)
    file_name = models.CharField(max_length=255, blank=True, default='')
    file_type = models.CharField(max_length=10, choices=FileType.choices, default=FileType.PDF)
    file_size = models.IntegerField(default=0)
    raw_text = models.TextField(blank=True, default='')
    parse_status = models.CharField(max_length=20, choices=ParseStatus.choices, default=ParseStatus.PENDING)
    parse_error = models.TextField(blank=True, default='')
    parsed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidates_resume'
        verbose_name = 'Candidate Resume'
        verbose_name_plural = 'Candidate Resumes'

    def __str__(self):
        return f"Resume for {self.candidate.name}"


class CandidateTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='tags',
    )
    tag = models.CharField(max_length=100, db_index=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tags',
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'candidates_tag'
        verbose_name = 'Candidate Tag'
        verbose_name_plural = 'Candidate Tags'
        unique_together = [('candidate', 'tag')]
        indexes = [
            models.Index(fields=['candidate', 'tag']),
        ]

    def __str__(self):
        return f"{self.tag} on {self.candidate.name}"
