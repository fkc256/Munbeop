from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "nickname", "is_staff", "created_at")
    search_fields = ("username", "email", "nickname")
    ordering = ("-created_at",)
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("프로필", {"fields": ("nickname",)}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("프로필", {"fields": ("email", "nickname")}),
    )
