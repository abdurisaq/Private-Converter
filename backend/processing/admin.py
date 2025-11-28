from django.contrib import admin
from .models import Job
# Register your models here.

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'input_filename', 'status', 'progress', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['input_filename', 'output_filename', 'user__email']
    readonly_fields = ['id', 'created_at', 'started_at', 'completed_at']