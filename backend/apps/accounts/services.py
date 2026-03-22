import logging

from django.db import transaction

from .models import User

logger = logging.getLogger(__name__)


@transaction.atomic
def register_user(email: str, password: str, full_name: str) -> User:
    """
    Register a new user.

    Args:
        email: User's email address (will be lowercased)
        password: Plain text password
        full_name: User's full name

    Returns:
        Newly created User instance
    """
    email = email.lower().strip()
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name.strip(),
    )
    logger.info("New user registered: %s (id=%s)", email, user.id)
    return user


@transaction.atomic
def create_organization_for_user(user: User, org_name: str):
    """
    Create a new organization and make the user its owner.

    Args:
        user: The User who will own the organization
        org_name: Display name for the organization

    Returns:
        Tuple of (Organization, Membership)
    """
    from apps.organizations.models import Organization, Membership
    from apps.organizations.services import generate_unique_slug

    slug = generate_unique_slug(org_name)
    organization = Organization.objects.create(
        name=org_name.strip(),
        slug=slug,
        created_by=user,
    )
    membership = Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
        is_active=True,
    )
    logger.info(
        "Organization '%s' (id=%s) created by user %s",
        org_name, organization.id, user.email
    )
    return organization, membership
