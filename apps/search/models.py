"""검색 로그 모델 — 실시간 검색어 랭킹용 (펨코 스타일).

3차에서는 단순 빈도 집계.
4차 임베딩 도입 시에도 그대로 활용 가능 (검색어 → 추천 시드).
"""
from django.conf import settings
from django.db import models


class SearchQuery(models.Model):
    """사용자 검색 로그. 실시간 검색어 랭킹/통계용."""

    query = models.CharField(max_length=500)
    keywords = models.CharField(
        max_length=500, blank=True, default="",
        help_text="extract_keywords 적용 결과 (조사 stripping 후), 쉼표 구분"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="search_queries",
        help_text="비로그인 사용자도 기록 (null)"
    )
    category = models.CharField(max_length=20, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["query", "created_at"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "검색 로그"
        verbose_name_plural = "검색 로그"

    def __str__(self) -> str:
        return f"{self.query[:30]} @ {self.created_at:%Y-%m-%d %H:%M}"
