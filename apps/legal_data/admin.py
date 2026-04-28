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
        "updated_at",
    )
    list_filter = ("category", "is_active", "law_name")
    search_fields = ("law_name", "article_number", "article_title", "content", "keywords")
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("law_name", "article_number")


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
    )
    list_filter = ("court", "result_type", "category", "judgment_date")
    search_fields = ("case_number", "case_name", "summary", "keywords")
    filter_horizontal = ("related_laws",)
    date_hierarchy = "judgment_date"
    readonly_fields = ("created_at", "updated_at")
