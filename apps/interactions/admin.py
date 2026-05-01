from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Bookmark, Comment, Like


def _admin_change_link(app_label: str, model_name: str, pk: int, label: str) -> str:
    try:
        url = reverse(f"admin:{app_label}_{model_name}_change", args=[pk])
    except Exception:
        return label
    return format_html('<a href="{}">{}</a>', url, label)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "story_link",
        "parent_id_display",
        "content_preview",
        "is_deleted",
        "like_count_display",
        "created_at",
    )
    list_filter = ("is_deleted", "created_at")
    search_fields = ("content", "user__username", "user__nickname", "story__title")
    raw_id_fields = ("story", "parent", "user")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    date_hierarchy = "created_at"
    actions = ("bulk_soft_delete", "bulk_restore")

    def get_queryset(self, request):
        return Comment.all_objects.select_related("user", "story", "parent")

    @admin.display(description="content")
    def content_preview(self, obj: Comment) -> str:
        text = obj.content or ""
        return text[:60] + ("…" if len(text) > 60 else "")

    @admin.display(description="parent")
    def parent_id_display(self, obj: Comment):
        return obj.parent_id or "-"

    @admin.display(description="story")
    def story_link(self, obj: Comment):
        if not obj.story_id:
            return "-"
        label = f"#{obj.story_id} {obj.story.title[:20]}" if obj.story else f"#{obj.story_id}"
        return _admin_change_link("stories", "story", obj.story_id, label)

    @admin.display(description="좋아요")
    def like_count_display(self, obj: Comment) -> int:
        return Like.objects.filter(target_type="comment", target_id=obj.id).count()

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
    list_display = ("id", "user", "target_type", "target_id", "target_link", "created_at")
    list_filter = ("target_type", "created_at")
    raw_id_fields = ("user",)
    search_fields = ("user__username", "user__nickname")

    @admin.display(description="대상")
    def target_link(self, obj: Like):
        if obj.target_type == "story":
            return _admin_change_link("stories", "story", obj.target_id, f"사연 #{obj.target_id}")
        if obj.target_type == "comment":
            return _admin_change_link("interactions", "comment", obj.target_id, f"댓글 #{obj.target_id}")
        return "-"


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "target_type", "target_id", "target_link", "created_at")
    list_filter = ("target_type", "created_at")
    raw_id_fields = ("user",)
    search_fields = ("user__username", "user__nickname")
    ordering = ("-created_at",)

    @admin.display(description="대상")
    def target_link(self, obj: Bookmark):
        if obj.target_type == "story":
            return _admin_change_link("stories", "story", obj.target_id, f"사연 #{obj.target_id}")
        if obj.target_type == "law":
            return _admin_change_link("legal_data", "law", obj.target_id, f"법령 #{obj.target_id}")
        if obj.target_type == "precedent":
            return _admin_change_link("legal_data", "precedent", obj.target_id, f"판례 #{obj.target_id}")
        return "-"
