from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'user_type', 'is_approved')
    list_editable = ('is_approved',)
    actions = ['approve_users']

    def approve_users(self, request, queryset):
        queryset.update(is_approved=True,is_active=True)
    approve_users.short_description = "Approve selected users"