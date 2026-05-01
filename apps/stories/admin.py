from django.contrib import admin
from django.utils import timezone

from .models import Category, Story


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
        "order",
        "story_count",
        "law_count",
        "precedent_count",
        "created_at",
    )
    list_editable = ("order",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "id")

    @admin.display(description="활성 사연")
    def story_count(self, obj: Category) -> int:
        return obj.stories.filter(is_deleted=False).count()

    @admin.display(description="법령")
    def law_count(self, obj: Category) -> int:
        return obj.laws.count()

    @admin.display(description="판례")
    def precedent_count(self, obj: Category) -> int:
        return obj.precedents.count()


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "user",
        "category",
        "view_count",
        "comment_count_display",
        "like_count_display",
        "is_anonymous",
        "is_deleted",
        "created_at",
    )
    list_filter = ("category", "is_deleted", "is_anonymous", "created_at")
    search_fields = ("title", "content", "user__username", "user__nickname")
    readonly_fields = (
        "view_count",
        "created_at",
        "updated_at",
        "deleted_at",
        "comment_count_display",
        "like_count_display",
    )
    raw_id_fields = ("user", "category")
    date_hierarchy = "created_at"
    actions = ("bulk_soft_delete", "bulk_restore", "bulk_hard_delete")

    def get_queryset(self, request):
        return Story.all_objects.select_related("user", "category")

    @admin.display(description="활성 댓글 수")
    def comment_count_display(self, obj: Story) -> int:
        return obj.comments.filter(is_deleted=False).count()

    @admin.display(description="좋아요 수")
    def like_count_display(self, obj: Story) -> int:
        from apps.interactions.models import Like

        return Like.objects.filter(target_type="story", target_id=obj.id).count()

    @admin.action(description="선택한 사연 soft delete")
    def bulk_soft_delete(self, request, queryset):
        updated = queryset.update(is_deleted=True, deleted_at=timezone.now())
        self.message_user(request, f"{updated}건 soft delete 처리됨.")

    @admin.action(description="선택한 사연 복구 (is_deleted=False)")
    def bulk_restore(self, request, queryset):
        updated = queryset.update(is_deleted=False, deleted_at=None)
        self.message_user(request, f"{updated}건 복구됨.")

    @admin.action(description="⚠️ 선택한 사연 진짜 삭제 (복구 불가)")
    def bulk_hard_delete(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count}건이 영구 삭제되었습니다 (복구 불가).")
