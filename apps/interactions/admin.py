from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Bookmark, Comment, Like, Report


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
        "deletion_reason",
        "report_count_display",
        "like_count_display",
        "created_at",
    )
    list_filter = ("is_deleted", "deletion_reason", "created_at")
    search_fields = ("content", "user__username", "user__nickname", "story__title")
    raw_id_fields = ("story", "parent", "user")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    date_hierarchy = "created_at"
    actions = ("bulk_soft_delete_admin", "bulk_restore", "bulk_soft_delete")

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

    @admin.display(description="신고")
    def report_count_display(self, obj: Comment) -> int:
        return obj.reports.count()

    @admin.action(description="⚠️ 선택한 댓글 관리자 직권 삭제 (deletion_reason='admin')")
    def bulk_soft_delete_admin(self, request, queryset):
        updated = queryset.update(
            is_deleted=True, deletion_reason="admin", deleted_at=timezone.now()
        )
        self.message_user(request, f"{updated}건 관리자 직권 삭제 처리됨.")

    @admin.action(description="선택한 댓글 일반 soft delete (작성자 명의)")
    def bulk_soft_delete(self, request, queryset):
        updated = queryset.update(
            is_deleted=True, deletion_reason="author", deleted_at=timezone.now()
        )
        self.message_user(request, f"{updated}건 soft delete 처리됨.")

    @admin.action(description="선택한 댓글 복구 (deletion_reason 초기화)")
    def bulk_restore(self, request, queryset):
        updated = queryset.update(
            is_deleted=False, deletion_reason="", deleted_at=None
        )
        self.message_user(request, f"{updated}건 복구됨.")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "comment_link", "reason", "created_at")
    list_filter = ("reason", "created_at")
    search_fields = ("user__username", "comment__content", "detail")
    raw_id_fields = ("user", "comment")
    readonly_fields = ("created_at",)

    @admin.display(description="신고 대상 댓글")
    def comment_link(self, obj: Report):
        if not obj.comment_id:
            return "-"
        text = obj.comment.content[:30] if obj.comment else f"#{obj.comment_id}"
        return _admin_change_link("interactions", "comment", obj.comment_id, text)


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
