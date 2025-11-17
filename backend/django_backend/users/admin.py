from django.contrib import admin
from .models import User
# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'role', 'is_active', 'storage_used', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['email', 'username']
    readonly_fields = ['storage_used', 'created_at', 'updated_at']
    fieldsets = (
        ('Personal Info', {'fields': ('email', 'username', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Storage', {'fields': ('storage_quota', 'storage_used')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
