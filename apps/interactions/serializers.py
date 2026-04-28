from rest_framework import serializers

from apps.legal_data.models import Law, Precedent
from apps.stories.models import Story

from .models import Bookmark, Comment, Like


DELETED_PLACEHOLDER = "삭제된 댓글입니다"


class CommentSerializer(serializers.ModelSerializer):
    """List/detail용. 1단계 대댓글 nested 포함."""

    user_nickname = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    is_reply = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            "id",
            "story",
            "parent",
            "user_id",
            "user_nickname",
            "content",
            "is_deleted",
            "is_reply",
            "is_owner",
            "like_count",
            "is_liked",
            "replies",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_user_id(self, obj: Comment):
        if obj.is_deleted:
            return None
        return obj.user_id

    def get_user_nickname(self, obj: Comment):
        if obj.is_deleted:
            return None
        if obj.user is None:
            return "(탈퇴 회원)"
        return obj.user.nickname

    def get_content(self, obj: Comment) -> str:
        if obj.is_deleted:
            return DELETED_PLACEHOLDER
        return obj.content

    def get_is_reply(self, obj: Comment) -> bool:
        return obj.parent_id is not None

    def get_is_owner(self, obj: Comment) -> bool:
        if obj.is_deleted:
            return False
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.user_id == request.user.id

    def get_like_count(self, obj: Comment) -> int:
        return Like.objects.filter(target_type="comment", target_id=obj.id).count()

    def get_is_liked(self, obj: Comment) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Like.objects.filter(
            user=request.user, target_type="comment", target_id=obj.id
        ).exists()

    def get_replies(self, obj: Comment):
        if obj.parent_id is not None:
            return []
        replies = obj.replies.all().order_by("created_at")
        # CommentManager에서 is_deleted=False 자동 필터 (default manager는 objects = CommentManager)
        # related accessor `obj.replies`는 related_manager — _default_manager가 사용됨
        # _default_manager는 objects (CommentManager) 이므로 자동 필터
        return CommentSerializer(replies, many=True, context=self.context).data


class CommentCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(min_length=1, max_length=1000)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(),  # 활성 댓글만 parent 후보
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Comment
        fields = ("id", "content", "parent")
        read_only_fields = ("id",)

    def validate(self, attrs):
        story = self.context["story"]
        parent = attrs.get("parent")
        if parent is not None:
            if parent.story_id != story.id:
                raise serializers.ValidationError(
                    {"parent": "다른 사연의 댓글에는 답글을 달 수 없습니다."}
                )
            if parent.parent_id is not None:
                raise serializers.ValidationError(
                    {"parent": "대댓글에는 다시 대댓글을 달 수 없습니다."}
                )
        return attrs


class CommentUpdateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(min_length=1, max_length=1000)

    class Meta:
        model = Comment
        fields = ("id", "content")
        read_only_fields = ("id",)


class LikeToggleSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=Like.TARGET_CHOICES)
    target_id = serializers.IntegerField(min_value=1)


class BookmarkToggleSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=Bookmark.TARGET_CHOICES)
    target_id = serializers.IntegerField(min_value=1)


class BookmarkListSerializer(serializers.ModelSerializer):
    target_data = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = ("id", "target_type", "target_id", "target_data", "created_at")
        read_only_fields = fields

    # TODO: 북마크 50건+ 시 N+1 최적화 (4차에서 처리)
    def get_target_data(self, obj: Bookmark):
        if obj.target_type == "story":
            s = Story.objects.filter(id=obj.target_id).select_related("category").first()
            if not s:
                return None
            return {
                "id": s.id,
                "title": s.title,
                "category": s.category.slug if s.category else None,
            }
        if obj.target_type == "law":
            l = Law.objects.filter(id=obj.target_id).first()
            if not l:
                return None
            return {
                "id": l.id,
                "law_name": l.law_name,
                "article_number": l.article_number,
                "article_title": l.article_title,
            }
        if obj.target_type == "precedent":
            p = Precedent.objects.filter(id=obj.target_id).first()
            if not p:
                return None
            return {
                "id": p.id,
                "case_number": p.case_number,
                "case_name": p.case_name,
                "court": p.court,
            }
        return None
