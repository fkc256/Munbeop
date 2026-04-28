from django.contrib import admin
from django.utils import timezone

from .models import Bookmark, Comment, Like


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "story",
        "parent",
        "short_content",
        "is_deleted",
        "created_at",
    )
    list_filter = ("is_deleted", "created_at")
    search_fields = ("content", "user__username", "user__nickname")
    raw_id_fields = ("story", "parent", "user")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    actions = ("bulk_soft_delete", "bulk_restore")

    def get_queryset(self, request):
        return Comment.all_objects.select_related("user", "story", "parent")

    @admin.display(description="content")
    def short_content(self, obj: Comment) -> str:
        return obj.content[:50]

    @admin.action(description="선택한 댓글 soft delete")
    def bulk_soft_delete(self, request, queryset):
        updated = queryset.update(is_deleted=True, deleted_at=timezone.now())
        self.message_user(request, f"{updated}건 soft delete 처리됨.")

    @admin.action(description="선택한 댓글 복구")
    def bulk_restore(self, request, queryset):
        updated = queryset.update(is_deleted=False, deleted_at=None)
        self.message_user(request, f"{updated}건 복구됨.")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "target_type", "target_id", "created_at")
    list_filter = ("target_type",)
    raw_id_fields = ("user",)


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "target_type", "target_id", "created_at")
    list_filter = ("target_type",)
    raw_id_fields = ("user",)
