from rest_framework import serializers

from .models import Organization, Membership
from apps.accounts.serializers import UserSerializer


class OrganizationSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'logo', 'website', 'industry', 'size',
            'created_by', 'created_at', 'updated_at', 'is_active', 'member_count',
        ]
        read_only_fields = ['id', 'slug', 'created_by', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.memberships.filter(is_active=True).count()


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['name', 'website', 'industry', 'size']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Organization name cannot be blank.")
        return value.strip()


class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = [
            'id', 'user', 'organization', 'role',
            'invited_by', 'joined_at', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'user', 'organization', 'invited_by', 'joined_at', 'created_at']


class MembershipListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ['id', 'user', 'role', 'joined_at', 'is_active']
        read_only_fields = ['id', 'user', 'joined_at']


class InviteMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=Membership.Role.choices, default=Membership.Role.MEMBER)


class UpdateMemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=Membership.Role.choices)
