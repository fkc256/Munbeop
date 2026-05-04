from django.contrib import admin

from .models import SearchQuery


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ("id", "query", "keywords", "user", "category", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("query", "keywords", "user__username")
    raw_id_fields = ("user",)
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
