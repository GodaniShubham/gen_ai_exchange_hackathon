from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("id", "email", "username", "otp", "otp_created_at", "is_verified", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "is_verified")
    
    fieldsets = (
        (None, {"fields": ("email", "username", "password", "otp", "otp_created_at", "is_verified")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
    )
    
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2", "otp", "otp_created_at", "is_verified", "is_staff", "is_active"),
        }),
    )
    
    search_fields = ("email", "username", "otp")
    ordering = ("email",)

admin.site.register(CustomUser, CustomUserAdmin)