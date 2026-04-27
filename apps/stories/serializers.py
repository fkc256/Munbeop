from rest_framework import serializers

from .models import Category, Story


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "order")
        read_only_fields = fields


def _author_display(story: Story) -> str:
    if story.is_anonymous:
        return "익명"
    if story.user is None:
        return "(탈퇴 회원)"
    return story.user.nickname


class StoryListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
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
        )
        read_only_fields = fields

    def get_author_display(self, obj: Story) -> str:
        return _author_display(obj)


class StoryDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    author_display = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = (
            "id",
            "title",
            "content",
            "category",
            "author_display",
            "is_anonymous",
            "is_owner",
            "view_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_author_display(self, obj: Story) -> str:
        return _author_display(obj)

    def get_is_owner(self, obj: Story) -> bool:
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return obj.user_id == request.user.id


class StoryCreateUpdateSerializer(serializers.ModelSerializer):
    title = serializers.CharField(min_length=5, max_length=200)
    content = serializers.CharField(min_length=10)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Story
        fields = ("id", "title", "content", "category", "is_anonymous")
        read_only_fields = ("id",)
