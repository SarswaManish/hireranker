from django.contrib import admin

from .models import Organization, Membership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'industry', 'size', 'is_active', 'created_by', 'created_at']
    list_filter = ['industry', 'size', 'is_active', 'created_at']
    search_fields = ['name', 'slug', 'website']
    readonly_fields = ['id', 'slug', 'created_at', 'updated_at']
    raw_id_fields = ['created_by']


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__email', 'organization__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['user', 'organization', 'invited_by']
