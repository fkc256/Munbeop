from rest_framework import serializers

from apps.legal_data.models import Law, Precedent
from apps.stories.models import Story

from .models import Bookmark, Comment, Like, Report


DELETION_PLACEHOLDERS = {
    "author": "삭제된 댓글입니다",
    "report": "신고에 의해 삭제된 댓글입니다",
    "admin": "관리자에 의해 삭제된 댓글입니다",
}
BEST_LIKE_THRESHOLD = 3  # 좋아요 N개 이상이면 베스트 댓글로 노출


class CommentSerializer(serializers.ModelSerializer):
    """List/detail용. 1단계 대댓글 nested + 좋아요 + 신고 + 베스트 + 작성자 뱃지."""

    user_nickname = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    is_reply = serializers.SerializerMethodField()
    is_best = serializers.SerializerMethodField()
    is_story_author = serializers.SerializerMethodField()
    deletion_label = serializers.SerializerMethodField()
    report_count = serializers.SerializerMethodField()
    is_reported_by_me = serializers.SerializerMethodField()

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
            "deletion_label",
            "is_reply",
            "is_owner",
            "is_story_author",
            "is_best",
            "like_count",
            "is_liked",
            "report_count",
            "is_reported_by_me",
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
            return DELETION_PLACEHOLDERS.get(obj.deletion_reason, "삭제된 댓글입니다")
        return obj.content

    def get_deletion_label(self, obj: Comment):
        """프론트가 색상/스타일 분기에 사용. 활성이면 None."""
        if not obj.is_deleted:
            return None
        return obj.deletion_reason or "author"

    def get_is_reply(self, obj: Comment) -> bool:
        return obj.parent_id is not None

    def get_is_owner(self, obj: Comment) -> bool:
        if obj.is_deleted:
            return False
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.user_id == request.user.id

    def get_is_story_author(self, obj: Comment) -> bool:
        """댓글 작성자가 사연 작성자인지 (커뮤니티 표준 '작성자' 뱃지)."""
        if obj.is_deleted or obj.user_id is None:
            return False
        return obj.story_id and obj.story.user_id == obj.user_id

    def get_like_count(self, obj: Comment) -> int:
        return Like.objects.filter(target_type="comment", target_id=obj.id).count()

    def get_is_liked(self, obj: Comment) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Like.objects.filter(
            user=request.user, target_type="comment", target_id=obj.id
        ).exists()

    def get_is_best(self, obj: Comment) -> bool:
        """좋아요 임계값 이상이면 베스트 댓글."""
        if obj.is_deleted:
            return False
        return self.get_like_count(obj) >= BEST_LIKE_THRESHOLD

    def get_report_count(self, obj: Comment) -> int:
        return obj.reports.count()

    def get_is_reported_by_me(self, obj: Comment) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.reports.filter(user=request.user).exists()

    def get_replies(self, obj: Comment):
        if obj.parent_id is not None:
            return []
        replies = obj.replies.all().order_by("created_at")
        return CommentSerializer(replies, many=True, context=self.context).data


class ReportCreateSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=Report.REASON_CHOICES)
    detail = serializers.CharField(required=False, allow_blank=True, max_length=500)


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
