import uuid

from django.db import models
from django.utils import timezone


class Organization(models.Model):
    class Industry(models.TextChoices):
        TECHNOLOGY = 'technology', 'Technology'
        FINANCE = 'finance', 'Finance'
        HEALTHCARE = 'healthcare', 'Healthcare'
        EDUCATION = 'education', 'Education'
        RETAIL = 'retail', 'Retail'
        MANUFACTURING = 'manufacturing', 'Manufacturing'
        CONSULTING = 'consulting', 'Consulting'
        MEDIA = 'media', 'Media'
        GOVERNMENT = 'government', 'Government'
        OTHER = 'other', 'Other'

    class Size(models.TextChoices):
        SOLO = '1', '1 (Solo)'
        SMALL = '2-10', '2-10'
        MEDIUM = '11-50', '11-50'
        LARGE = '51-200', '51-200'
        ENTERPRISE = '201-1000', '201-1000'
        XLARGE = '1000+', '1000+'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    website = models.URLField(blank=True, default='')
    industry = models.CharField(max_length=50, choices=Industry.choices, blank=True, default='')
    size = models.CharField(max_length=20, choices=Size.choices, blank=True, default='')
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_organizations',
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'organizations_organization'
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    invited_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_invitations',
    )
    joined_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organizations_membership'
        verbose_name = 'Membership'
        verbose_name_plural = 'Memberships'
        unique_together = [('user', 'organization')]
        indexes = [
            models.Index(fields=['user', 'organization']),
            models.Index(fields=['organization', 'role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.user.email} @ {self.organization.name} ({self.role})"
