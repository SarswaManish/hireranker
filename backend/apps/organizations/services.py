import logging
import re

from django.db import transaction
from django.utils.text import slugify

from .models import Organization, Membership

logger = logging.getLogger(__name__)


def generate_unique_slug(name: str) -> str:
    """Generate a unique slug for an organization name."""
    base_slug = slugify(name)[:100]
    if not base_slug:
        base_slug = 'org'

    slug = base_slug
    counter = 1
    while Organization.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


@transaction.atomic
def invite_member(organization: Organization, email: str, role: str, invited_by) -> Membership:
    """
    Invite a user to an organization by email.
    If user doesn't exist, they will be linked when they register.
    If user exists, creates membership immediately.
    """
    from apps.accounts.models import User

    try:
        user = User.objects.get(email=email.lower())
    except User.DoesNotExist:
        raise ValueError(f"No user found with email {email}")

    membership, created = Membership.objects.get_or_create(
        user=user,
        organization=organization,
        defaults={
            'role': role,
            'invited_by': invited_by,
            'is_active': True,
        }
    )
    if not created and not membership.is_active:
        membership.is_active = True
        membership.role = role
        membership.save()

    logger.info(
        "Member %s added to org %s with role %s by %s",
        email, organization.name, role, invited_by.email
    )
    return membership


@transaction.atomic
def remove_member(organization: Organization, user) -> None:
    """Remove a user from an organization."""
    Membership.objects.filter(
        user=user,
        organization=organization,
    ).update(is_active=False)
    logger.info("Member %s removed from org %s", user.email, organization.name)


def get_user_organizations(user):
    """Get all active organizations for a user."""
    return Organization.objects.filter(
        memberships__user=user,
        memberships__is_active=True,
        is_active=True,
    ).select_related('created_by')


def get_user_role_in_org(user, organization) -> str | None:
    """Get a user's role in an organization, or None if not a member."""
    try:
        membership = Membership.objects.get(
            user=user,
            organization=organization,
            is_active=True,
        )
        return membership.role
    except Membership.DoesNotExist:
        return None
