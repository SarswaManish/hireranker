from django.contrib import admin

from .models import Candidate, CandidateImportBatch, CandidateResume, CandidateTag


@admin.register(CandidateImportBatch)
class CandidateImportBatchAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'project', 'status', 'total_rows', 'processed_rows', 'failed_rows', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['file_name', 'project__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['project', 'imported_by']


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'project', 'status', 'is_duplicate', 'created_at']
    list_filter = ['status', 'is_duplicate', 'created_at']
    search_fields = ['name', 'email', 'college']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['project', 'batch', 'duplicate_of']
    list_select_related = ['project']


@admin.register(CandidateResume)
class CandidateResumeAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'file_type', 'file_size', 'parse_status', 'parsed_at']
    list_filter = ['file_type', 'parse_status']
    search_fields = ['candidate__name', 'candidate__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['candidate']


@admin.register(CandidateTag)
class CandidateTagAdmin(admin.ModelAdmin):
    list_display = ['tag', 'candidate', 'created_by', 'created_at']
    list_filter = ['tag', 'created_at']
    search_fields = ['tag', 'candidate__name']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['candidate', 'created_by']
