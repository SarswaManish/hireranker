import uuid

from django.db import models
from django.utils import timezone


class HiringProject(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ACTIVE = 'active', 'Active'
        CLOSED = 'closed', 'Closed'
        ARCHIVED = 'archived', 'Archived'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='projects',
    )
    name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, default='')
    role_title = models.CharField(max_length=255)
    job_description = models.TextField()
    must_have_skills = models.JSONField(default=list)
    good_to_have_skills = models.JSONField(default=list)
    min_experience_years = models.FloatField(null=True, blank=True)
    location_preference = models.CharField(max_length=255, blank=True, default='')
    degree_requirement = models.CharField(max_length=255, blank=True, default='')
    notice_period_days = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects',
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects_hiring_project'
        verbose_name = 'Hiring Project'
        verbose_name_plural = 'Hiring Projects'
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class JobDescriptionSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        HiringProject,
        on_delete=models.CASCADE,
        related_name='jd_snapshots',
    )
    raw_text = models.TextField()
    structured_requirements = models.JSONField(default=dict)
    parsed_at = models.DateTimeField(null=True, blank=True)
    parser_version = models.CharField(max_length=50, default='1.0')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'projects_jd_snapshot'
        verbose_name = 'JD Snapshot'
        verbose_name_plural = 'JD Snapshots'
        ordering = ['-created_at']

    def __str__(self):
        return f"JD Snapshot for {self.project.name} @ {self.created_at}"
