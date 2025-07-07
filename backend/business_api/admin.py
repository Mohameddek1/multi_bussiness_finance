from django.contrib import admin
from .models import Business, UserBusinessRole


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'currency', 'fiscal_year_start', 'created_at']
    list_filter = ['currency', 'fiscal_year_start', 'created_at']
    search_fields = ['name', 'owner__username', 'owner__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'owner')
        }),
        ('Business Settings', {
            'fields': ('currency', 'fiscal_year_start', 'default_language', 'logo')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserBusinessRole)
class UserBusinessRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'business', 'role', 'assigned_at', 'assigned_by']
    list_filter = ['role', 'assigned_at']
    search_fields = ['user__username', 'user__email', 'business__name']
    readonly_fields = ['assigned_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'business', 'assigned_by')
