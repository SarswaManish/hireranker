from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'user', 'ip_address', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['event_type', 'user__email', 'ip_address']
    readonly_fields = ['id', 'user', 'event_type', 'metadata', 'ip_address', 'user_agent', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
