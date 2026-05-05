from django.contrib import admin
from .models import Meeting, UploadSession, Transcript, Summary, MOM

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_type', 'status', 'created_at']
    list_filter = ['status', 'file_type']
    search_fields = ['title', 'original_filename']

@admin.register(UploadSession)
class UploadSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'meeting', 'received_chunks', 'total_chunks', 'status']

admin.site.register(Transcript)
admin.site.register(Summary)
admin.site.register(MOM)
