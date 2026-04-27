from django.contrib import admin
from django.utils import timezone

from .models import Category, Story


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "order", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "id")


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "user",
        "category",
        "view_count",
        "is_deleted",
        "created_at",
    )
    list_filter = ("category", "is_deleted", "created_at")
    search_fields = ("title", "content", "user__username", "user__nickname")
    readonly_fields = ("view_count", "created_at", "updated_at", "deleted_at")
    actions = ("bulk_soft_delete", "bulk_restore")

    def get_queryset(self, request):
        return Story.all_objects.select_related("user", "category")

    @admin.action(description="선택한 사연 soft delete")
    def bulk_soft_delete(self, request, queryset):
        updated = queryset.update(is_deleted=True, deleted_at=timezone.now())
        self.message_user(request, f"{updated}건 soft delete 처리됨.")

    @admin.action(description="선택한 사연 복구 (is_deleted=False)")
    def bulk_restore(self, request, queryset):
        updated = queryset.update(is_deleted=False, deleted_at=None)
        self.message_user(request, f"{updated}건 복구됨.")
