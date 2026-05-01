from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "nickname",
        "is_active",
        "is_staff",
        "date_joined",
        "story_count",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "date_joined")
    search_fields = ("username", "email", "nickname")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login", "created_at", "updated_at")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("프로필", {"fields": ("nickname",)}),
        ("타임스탬프", {"fields": ("created_at", "updated_at")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("프로필", {"fields": ("email", "nickname")}),
    )
    actions = ("activate_users", "deactivate_users")

    @admin.display(description="활성 사연 수")
    def story_count(self, obj: User) -> int:
        return obj.stories.filter(is_deleted=False).count()

    @admin.action(description="선택한 사용자 활성화")
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated}명 활성화됨.")

    @admin.action(description="선택한 사용자 비활성화 (로그인 차단)")
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated}명 비활성화됨. 로그인 차단됨.")
