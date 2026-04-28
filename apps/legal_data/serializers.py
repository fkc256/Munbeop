from rest_framework import serializers

from apps.stories.serializers import CategorySerializer

from .models import Law, Precedent


class LawMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Law
        fields = ("id", "law_name", "article_number", "article_title")
        read_only_fields = fields


class PrecedentMiniSerializer(serializers.ModelSerializer):
    result_type_display = serializers.SerializerMethodField()

    class Meta:
        model = Precedent
        fields = (
            "id",
            "case_number",
            "case_name",
            "court",
            "judgment_date",
            "result_type_display",
        )
        read_only_fields = fields

    def get_result_type_display(self, obj: Precedent) -> str:
        return obj.get_result_type_display()


class LawListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Law
        fields = (
            "id",
            "law_name",
            "article_number",
            "article_title",
            "category",
            "keywords",
        )
        read_only_fields = fields


class LawDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    related_precedents = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Law
        fields = (
            "id",
            "law_name",
            "article_number",
            "article_title",
            "content",
            "category",
            "keywords",
            "source_url",
            "is_active",
            "related_precedents",
            "is_bookmarked",
        )
        read_only_fields = fields

    def get_related_precedents(self, obj: Law):
        recent = obj.precedents.all().order_by("-judgment_date")[:5]
        return PrecedentMiniSerializer(recent, many=True).data

    def get_is_bookmarked(self, obj: Law) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        from apps.interactions.models import Bookmark

        return Bookmark.objects.filter(
            user=request.user, target_type="law", target_id=obj.id
        ).exists()


class PrecedentListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
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
        )
        read_only_fields = fields

    def get_result_type_display(self, obj: Precedent) -> str:
        return obj.get_result_type_display()


class PrecedentDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    result_type_display = serializers.SerializerMethodField()
    related_laws = LawMiniSerializer(many=True, read_only=True)
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Precedent
        fields = (
            "id",
            "case_number",
            "case_name",
            "court",
            "judgment_date",
            "summary",
            "content",
            "category",
            "result_type",
            "result_type_display",
            "keywords",
            "source_url",
            "related_laws",
            "is_bookmarked",
        )
        read_only_fields = fields

    def get_result_type_display(self, obj: Precedent) -> str:
        return obj.get_result_type_display()

    def get_is_bookmarked(self, obj: Precedent) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        from apps.interactions.models import Bookmark

        return Bookmark.objects.filter(
            user=request.user, target_type="precedent", target_id=obj.id
        ).exists()
