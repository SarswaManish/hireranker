import logging

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Organization, Membership
from .serializers import (
    OrganizationSerializer,
    OrganizationCreateSerializer,
    MembershipSerializer,
    MembershipListSerializer,
    InviteMemberSerializer,
    UpdateMemberRoleSerializer,
)
from .services import generate_unique_slug, invite_member, remove_member
from core.permissions import IsOrganizationMember, IsOrganizationAdmin, IsOrganizationOwner
from core.utils import log_event, AuditEventType

logger = logging.getLogger(__name__)


class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return Organization.objects.filter(
            memberships__user=self.request.user,
            memberships__is_active=True,
            is_active=True,
        ).select_related('created_by').distinct()

    def get_serializer_class(self):
        if self.action in ['create']:
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def create(self, request, *args, **kwargs):
        serializer = OrganizationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        validated = serializer.validated_data
        slug = generate_unique_slug(validated['name'])
        org = Organization.objects.create(
            **validated,
            slug=slug,
            created_by=request.user,
        )
        Membership.objects.create(
            user=request.user,
            organization=org,
            role=Membership.Role.OWNER,
        )
        log_event(request.user, AuditEventType.PROJECT_CREATED, {'org_id': str(org.id), 'org_name': org.name})
        return Response(
            {'data': OrganizationSerializer(org).data, 'message': 'Organization created', 'errors': None},
            status=status.HTTP_201_CREATED
        )

    def retrieve(self, request, *args, **kwargs):
        org = self.get_object()
        return Response(
            {'data': OrganizationSerializer(org).data, 'message': None, 'errors': None}
        )

    def update(self, request, *args, **kwargs):
        org = self.get_object()
        membership = get_object_or_404(Membership, user=request.user, organization=org, is_active=True)
        if membership.role not in [Membership.Role.OWNER, Membership.Role.ADMIN]:
            return Response(
                {'data': None, 'message': 'Permission denied', 'errors': None},
                status=status.HTTP_403_FORBIDDEN
            )
        partial = kwargs.pop('partial', False)
        serializer = OrganizationSerializer(org, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response(
            {'data': serializer.data, 'message': 'Organization updated', 'errors': None}
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        org = self.get_object()
        membership = get_object_or_404(Membership, user=request.user, organization=org, is_active=True)
        if membership.role != Membership.Role.OWNER:
            return Response(
                {'data': None, 'message': 'Only owner can delete organization', 'errors': None},
                status=status.HTTP_403_FORBIDDEN
            )
        org.is_active = False
        org.save()
        return Response(
            {'data': None, 'message': 'Organization deactivated', 'errors': None},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        org = self.get_object()
        memberships = Membership.objects.filter(
            organization=org,
            is_active=True,
        ).select_related('user').order_by('joined_at')
        serializer = MembershipListSerializer(memberships, many=True)
        return Response(
            {'data': serializer.data, 'message': None, 'errors': None}
        )

    @action(detail=True, methods=['post'], url_path='members/invite')
    def invite_member(self, request, pk=None):
        org = self.get_object()
        membership = get_object_or_404(Membership, user=request.user, organization=org, is_active=True)
        if membership.role not in [Membership.Role.OWNER, Membership.Role.ADMIN]:
            return Response(
                {'data': None, 'message': 'Permission denied', 'errors': None},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = InviteMemberSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            new_membership = invite_member(
                organization=org,
                email=serializer.validated_data['email'],
                role=serializer.validated_data['role'],
                invited_by=request.user,
            )
        except ValueError as e:
            return Response(
                {'data': None, 'message': str(e), 'errors': None},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(
            {'data': MembershipSerializer(new_membership).data, 'message': 'Member invited', 'errors': None},
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['delete'], url_path='members/(?P<user_id>[^/.]+)')
    def remove_member(self, request, pk=None, user_id=None):
        org = self.get_object()
        membership = get_object_or_404(Membership, user=request.user, organization=org, is_active=True)
        if membership.role not in [Membership.Role.OWNER, Membership.Role.ADMIN]:
            return Response(
                {'data': None, 'message': 'Permission denied', 'errors': None},
                status=status.HTTP_403_FORBIDDEN
            )
        from apps.accounts.models import User
        target_user = get_object_or_404(User, id=user_id)
        target_membership = get_object_or_404(Membership, user=target_user, organization=org, is_active=True)
        if target_membership.role == Membership.Role.OWNER:
            return Response(
                {'data': None, 'message': 'Cannot remove owner', 'errors': None},
                status=status.HTTP_400_BAD_REQUEST
            )
        remove_member(org, target_user)
        return Response(
            {'data': None, 'message': 'Member removed', 'errors': None},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['patch'], url_path='members/(?P<user_id>[^/.]+)/role')
    def update_member_role(self, request, pk=None, user_id=None):
        org = self.get_object()
        membership = get_object_or_404(Membership, user=request.user, organization=org, is_active=True)
        if membership.role != Membership.Role.OWNER:
            return Response(
                {'data': None, 'message': 'Only owner can change roles', 'errors': None},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = UpdateMemberRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        from apps.accounts.models import User
        target_user = get_object_or_404(User, id=user_id)
        target_membership = get_object_or_404(Membership, user=target_user, organization=org, is_active=True)
        target_membership.role = serializer.validated_data['role']
        target_membership.save()
        return Response(
            {'data': MembershipSerializer(target_membership).data, 'message': 'Role updated', 'errors': None}
        )
