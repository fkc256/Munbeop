from django.contrib import admin

from .models import Law, Precedent


@admin.register(Law)
class LawAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "law_name",
        "article_number",
        "article_title",
        "category",
        "is_active",
        "precedent_count_display",
        "bookmark_count_display",
        "updated_at",
    )
    list_filter = ("category", "is_active", "law_name")
    list_editable = ("is_active",)
    search_fields = (
        "law_name",
        "article_number",
        "article_title",
        "content",
        "keywords",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "precedent_count_display",
        "bookmark_count_display",
    )
    raw_id_fields = ("category",)
    ordering = ("law_name", "article_number")
    actions = ("activate_laws", "deactivate_laws")

    @admin.display(description="연결 판례 수")
    def precedent_count_display(self, obj: Law) -> int:
        return obj.precedents.count()

    @admin.display(description="북마크 수")
    def bookmark_count_display(self, obj: Law) -> int:
        from apps.interactions.models import Bookmark

        return Bookmark.objects.filter(target_type="law", target_id=obj.id).count()

    @admin.action(description="선택한 법령 활성화 (is_active=True)")
    def activate_laws(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated}건 활성화됨.")

    @admin.action(description="선택한 법령 비활성화 (폐지 등)")
    def deactivate_laws(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated}건 비활성화됨. API 응답에서 제외됨.")


@admin.register(Precedent)
class PrecedentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case_number",
        "case_name",
        "court",
        "judgment_date",
        "category",
        "result_type",
        "related_laws_count",
        "bookmark_count_display",
        "updated_at",
    )
    list_filter = ("court", "result_type", "category", "judgment_date")
    search_fields = ("case_number", "case_name", "summary", "content", "keywords")
    filter_horizontal = ("related_laws",)
    raw_id_fields = ("category",)
    date_hierarchy = "judgment_date"
    readonly_fields = (
        "created_at",
        "updated_at",
        "related_laws_count",
        "bookmark_count_display",
    )

    @admin.display(description="연결 법령 수")
    def related_laws_count(self, obj: Precedent) -> int:
        return obj.related_laws.count()

    @admin.display(description="북마크 수")
    def bookmark_count_display(self, obj: Precedent) -> int:
        from apps.interactions.models import Bookmark

        return Bookmark.objects.filter(target_type="precedent", target_id=obj.id).count()
