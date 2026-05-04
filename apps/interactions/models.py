from django.conf import settings
from django.db import models
from django.utils import timezone


class CommentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Comment(models.Model):
    DELETION_REASONS = [
        ("author", "작성자 본인 삭제"),
        ("report", "신고 누적 자동 삭제"),
        ("admin", "관리자 수동 삭제"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="comments",
    )
    story = models.ForeignKey(
        "stories.Story",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )
    content = models.TextField()
    is_deleted = models.BooleanField(default=False)
    deletion_reason = models.CharField(
        max_length=20, choices=DELETION_REASONS, blank=True, default=""
    )
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CommentManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["story", "created_at"]),
            models.Index(fields=["parent"]),
        ]
        verbose_name = "댓글"
        verbose_name_plural = "댓글"

    def __str__(self) -> str:
        prefix = "↳ " if self.parent_id else ""
        return f"{prefix}[{self.story_id}] {self.content[:30]}"

    @property
    def is_reply(self) -> bool:
        return self.parent_id is not None

    def soft_delete(self, reason: str = "author") -> None:
        self.is_deleted = True
        self.deletion_reason = reason
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deletion_reason", "deleted_at"])


class Like(models.Model):
    TARGET_CHOICES = [
        ("story", "사연"),
        ("comment", "댓글"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    target_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "target_type", "target_id"]]
        indexes = [
            models.Index(fields=["target_type", "target_id"]),
        ]
        verbose_name = "좋아요"
        verbose_name_plural = "좋아요"

    def __str__(self) -> str:
        return f"{self.user_id} likes {self.target_type}#{self.target_id}"


class Report(models.Model):
    """댓글 신고. 같은 사용자가 같은 댓글에 여러 번 신고 X.
    임계값(REPORT_THRESHOLD) 누적 시 댓글 자동 soft delete (deletion_reason='report').
    """
    REASON_CHOICES = [
        ("spam", "스팸/광고"),
        ("abuse", "욕설/비방"),
        ("misinfo", "허위정보"),
        ("obscene", "음란/혐오"),
        ("etc", "기타"),
    ]
    REPORT_THRESHOLD = 3  # 이 건수에 도달하면 자동 삭제

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    comment = models.ForeignKey(
        "interactions.Comment",
        on_delete=models.CASCADE,
        related_name="reports",
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default="etc")
    detail = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "comment"]]
        indexes = [models.Index(fields=["comment", "created_at"])]
        verbose_name = "신고"
        verbose_name_plural = "신고"

    def __str__(self) -> str:
        return f"report by {self.user_id} on comment {self.comment_id} ({self.reason})"


class Bookmark(models.Model):
    TARGET_CHOICES = [
        ("story", "사연"),
        ("law", "법령"),
        ("precedent", "판례"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookmarks",
    )
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    target_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "target_type", "target_id"]]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "target_type"]),
        ]
        verbose_name = "북마크"
        verbose_name_plural = "북마크"

    def __str__(self) -> str:
        return f"{self.user_id} bookmarks {self.target_type}#{self.target_id}"
