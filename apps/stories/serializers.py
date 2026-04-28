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


class _StoryInteractionMixin(serializers.ModelSerializer):
    """Story 응답에 댓글/좋아요/북마크 필드 추가 (interactions 앱과의 통합)."""

    comment_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    def get_comment_count(self, obj: Story) -> int:
        # 어노테이션 우선, 없으면 직접 카운트 (단일 객체 retrieve 등)
        cached = getattr(obj, "_comment_count", None)
        if cached is not None:
            return cached
        from apps.interactions.models import Comment

        return Comment.objects.filter(story=obj).count()

    def get_like_count(self, obj: Story) -> int:
        cached = getattr(obj, "_like_count", None)
        if cached is not None:
            return cached
        from apps.interactions.models import Like

        return Like.objects.filter(target_type="story", target_id=obj.id).count()

    def get_is_liked(self, obj: Story) -> bool:
        cached = getattr(obj, "_is_liked", None)
        if cached is not None:
            return bool(cached)
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        from apps.interactions.models import Like

        return Like.objects.filter(
            user=request.user, target_type="story", target_id=obj.id
        ).exists()

    def get_is_bookmarked(self, obj: Story) -> bool:
        cached = getattr(obj, "_is_bookmarked", None)
        if cached is not None:
            return bool(cached)
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        from apps.interactions.models import Bookmark

        return Bookmark.objects.filter(
            user=request.user, target_type="story", target_id=obj.id
        ).exists()


class StoryListSerializer(_StoryInteractionMixin):
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
            "comment_count",
            "like_count",
            "is_liked",
            "is_bookmarked",
            "created_at",
        )
        read_only_fields = fields

    def get_author_display(self, obj: Story) -> str:
        return _author_display(obj)


class StoryDetailSerializer(_StoryInteractionMixin):
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
            "comment_count",
            "like_count",
            "is_liked",
            "is_bookmarked",
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
