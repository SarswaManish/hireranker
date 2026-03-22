import logging

from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


def get_user_org_membership(user, organization):
    """Get user's membership in an organization or None."""
    from apps.organizations.models import Membership
    return Membership.objects.filter(
        user=user,
        organization=organization,
        is_active=True,
    ).first()


class IsOrganizationMember(BasePermission):
    """
    Requires the user to be an active member of the organization.
    The view must set self.organization or the request must have organization available.
    """
    message = 'You must be a member of this organization.'

    def has_object_permission(self, request, view, obj):
        from apps.organizations.models import Organization, Membership

        if isinstance(obj, Organization):
            org = obj
        elif hasattr(obj, 'organization'):
            org = obj.organization
        else:
            return False

        return Membership.objects.filter(
            user=request.user,
            organization=org,
            is_active=True,
        ).exists()


class IsOrganizationAdmin(BasePermission):
    """Requires owner or admin role."""
    message = 'You must be an admin or owner of this organization.'

    def has_object_permission(self, request, view, obj):
        from apps.organizations.models import Organization, Membership

        if isinstance(obj, Organization):
            org = obj
        elif hasattr(obj, 'organization'):
            org = obj.organization
        else:
            return False

        return Membership.objects.filter(
            user=request.user,
            organization=org,
            role__in=['owner', 'admin'],
            is_active=True,
        ).exists()


class IsOrganizationOwner(BasePermission):
    """Requires owner role."""
    message = 'You must be the owner of this organization.'

    def has_object_permission(self, request, view, obj):
        from apps.organizations.models import Organization, Membership

        if isinstance(obj, Organization):
            org = obj
        elif hasattr(obj, 'organization'):
            org = obj.organization
        else:
            return False

        return Membership.objects.filter(
            user=request.user,
            organization=org,
            role='owner',
            is_active=True,
        ).exists()
