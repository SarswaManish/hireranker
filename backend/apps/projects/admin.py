from django.contrib import admin

from .models import HiringProject, JobDescriptionSnapshot


@admin.register(HiringProject)
class HiringProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'role_title', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'role_title', 'company_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['organization', 'created_by']
    list_select_related = ['organization', 'created_by']


@admin.register(JobDescriptionSnapshot)
class JobDescriptionSnapshotAdmin(admin.ModelAdmin):
    list_display = ['project', 'parsed_at', 'parser_version', 'created_at']
    list_filter = ['parser_version', 'created_at']
    search_fields = ['project__name']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['project']
