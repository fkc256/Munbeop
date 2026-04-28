from django.db import models


class Law(models.Model):
    law_name = models.CharField(max_length=100, db_index=True)
    article_number = models.CharField(max_length=50)
    article_title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    category = models.ForeignKey(
        "stories.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laws",
    )
    keywords = models.CharField(
        max_length=500,
        blank=True,
        help_text="쉼표로 구분된 검색 키워드",
    )
    source_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["law_name", "article_number"]
        unique_together = [["law_name", "article_number"]]
        indexes = [
            models.Index(fields=["law_name"]),
            models.Index(fields=["category"]),
        ]
        verbose_name = "법령"
        verbose_name_plural = "법령"

    def __str__(self) -> str:
        return f"{self.law_name} {self.article_number}"


class Precedent(models.Model):
    RESULT_CHOICES = [
        ("plaintiff_win", "원고승"),
        ("plaintiff_partial", "원고일부승"),
        ("defendant_win", "원고패"),
        ("settled", "조정/화해"),
        ("etc", "기타"),
    ]

    case_number = models.CharField(max_length=100, db_index=True)
    case_name = models.CharField(max_length=300)
    court = models.CharField(max_length=100, db_index=True)
    judgment_date = models.DateField(db_index=True)
    summary = models.TextField(help_text="판결 요지")
    content = models.TextField(help_text="판례 본문 또는 발췌")
    category = models.ForeignKey(
        "stories.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="precedents",
    )
    related_laws = models.ManyToManyField(
        Law,
        blank=True,
        related_name="precedents",
    )
    keywords = models.CharField(max_length=500, blank=True)
    source_url = models.URLField(blank=True)
    result_type = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default="etc",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-judgment_date"]
        unique_together = [["case_number", "court"]]
        indexes = [
            models.Index(fields=["court", "-judgment_date"]),
            models.Index(fields=["category"]),
        ]
        verbose_name = "판례"
        verbose_name_plural = "판례"

    def __str__(self) -> str:
        return f"[{self.court}] {self.case_number} {self.case_name}"
