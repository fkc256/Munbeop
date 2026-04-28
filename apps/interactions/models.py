from django.conf import settings
from django.db import models
from django.utils import timezone


class CommentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Comment(models.Model):
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

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])


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
