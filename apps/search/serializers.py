from rest_framework import serializers

from apps.legal_data.models import Law, Precedent
from apps.stories.models import Story


def _truncate(text: str, n: int) -> str:
    text = text or ""
    if len(text) <= n:
        return text
    return text[:n] + "…"


class _ScoredMixin(serializers.ModelSerializer):
    matched_keywords = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    def get_matched_keywords(self, obj) -> list[str]:
        return getattr(obj, "_matched_keywords", [])

    def get_score(self, obj) -> int:
        return getattr(obj, "_score", 0)


class LawSearchResultSerializer(_ScoredMixin):
    category = serializers.SlugRelatedField(read_only=True, slug_field="slug")
    content_preview = serializers.SerializerMethodField()

    class Meta:
        model = Law
        fields = (
            "id",
            "law_name",
            "article_number",
            "article_title",
            "category",
            "content_preview",
            "matched_keywords",
            "score",
        )
        read_only_fields = fields

    def get_content_preview(self, obj: Law) -> str:
        return _truncate(obj.content, 100)


class PrecedentSearchResultSerializer(_ScoredMixin):
    category = serializers.SlugRelatedField(read_only=True, slug_field="slug")
    summary_preview = serializers.SerializerMethodField()
    result_type_display = serializers.SerializerMethodField()

    class Meta:
        model = Precedent
        fields = (
            "id",
            "case_number",
            "case_name",
            "court",
            "judgment_date",
            "category",
            "result_type",
            "result_type_display",
            "summary_preview",
            "matched_keywords",
            "score",
        )
        read_only_fields = fields

    def get_summary_preview(self, obj: Precedent) -> str:
        return _truncate(obj.summary, 150)

    def get_result_type_display(self, obj: Precedent) -> str:
        return obj.get_result_type_display()


class StorySearchResultSerializer(_ScoredMixin):
    category = serializers.SlugRelatedField(read_only=True, slug_field="slug")
    content_preview = serializers.SerializerMethodField()
    author_display = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = (
            "id",
            "title",
            "category",
            "author_display",
            "view_count",
            "created_at",
            "content_preview",
            "matched_keywords",
            "score",
        )
        read_only_fields = fields

    def get_content_preview(self, obj: Story) -> str:
        return _truncate(obj.content, 100)

    def get_author_display(self, obj: Story) -> str:
        if obj.is_anonymous:
            return "익명"
        if obj.user is None:
            return "(탈퇴 회원)"
        return obj.user.nickname
