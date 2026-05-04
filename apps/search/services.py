"""도메인별 검색 함수 (3차 — 키워드 ILIKE 매칭).

⚠️ 4차 업그레이드 시 교체 포인트:
- ``search_laws/precedents/stories`` 의 매칭 로직(Q-OR icontains)을
  임베딩 코사인 유사도 기반 매칭으로 교체.
- 함수 시그니처(keywords/category/limit/exclude_id)와 반환 형식
  (인스턴스에 ``_matched_keywords``, ``_score`` 부착)은 유지하면
  Serializer/View는 그대로 사용 가능.
"""
from __future__ import annotations

from typing import Iterable, Optional

from django.db.models import Count, Q

from apps.legal_data.models import Law, Precedent
from apps.stories.models import Story


def _kw_in_any(kw: str, *fields: Optional[str]) -> bool:
    """case-insensitive substring 매칭. 한글에는 영향 없고 영문 혼합 안전."""
    kw_l = kw.lower()
    return any(kw_l in (f or "").lower() for f in fields)


def _build_or_q(keywords: Iterable[str], field_names: Iterable[str]) -> Q:
    q = Q()
    for kw in keywords:
        for f in field_names:
            q |= Q(**{f"{f}__icontains": kw})
    return q


def search_laws(
    keywords: list[str],
    category: Optional[str] = None,
    limit: int = 5,
) -> list[Law]:
    if not keywords:
        return []
    qs = Law.objects.filter(is_active=True).select_related("category")
    if category:
        qs = qs.filter(category__slug=category)
    qs = qs.filter(_build_or_q(keywords, ("law_name", "keywords", "content"))).distinct()

    scored: list[Law] = []
    for law in qs:
        matched = [
            kw for kw in keywords
            if _kw_in_any(kw, law.law_name, law.keywords, law.content)
        ]
        law._matched_keywords = matched
        law._score = len(matched)
        scored.append(law)
    scored.sort(key=lambda l: (l._score, l.updated_at), reverse=True)
    return scored[:limit]


def search_precedents(
    keywords: list[str],
    category: Optional[str] = None,
    limit: int = 10,
) -> list[Precedent]:
    if not keywords:
        return []
    qs = (
        Precedent.objects.select_related("category")
        .prefetch_related("related_laws")
    )
    if category:
        qs = qs.filter(category__slug=category)
    qs = qs.filter(
        _build_or_q(keywords, ("case_name", "keywords", "summary", "content"))
    ).distinct()

    scored: list[Precedent] = []
    for p in qs:
        matched = [
            kw for kw in keywords
            if _kw_in_any(kw, p.case_name, p.keywords, p.summary, p.content)
        ]
        p._matched_keywords = matched
        p._score = len(matched)
        scored.append(p)
    scored.sort(key=lambda p: (p._score, p.judgment_date), reverse=True)
    return scored[:limit]


def search_stories(
    keywords: list[str],
    category: Optional[str] = None,
    limit: int = 5,
    exclude_id: Optional[int] = None,
) -> list[Story]:
    """유사 사연 추천 — 키워드 매칭 + engagement(view/like/comment) 가중 합산.

    3차 알고리즘 (의도적으로 단순):
      composite = 키워드 매칭 점수 × 3
                + log10(view_count + 1)
                + 0.5 × like_count
                + 1.0 × comment_count

    핀터레스트/유튜브식 의미적 유사도(임베딩 + 협업필터링)는 4차 영역 — search_stories
    함수 시그니처는 동일하게 유지해서 4차에서 swap만 하면 ViewSet 변경 없음.
    """
    import math

    from apps.interactions.models import Comment, Like

    if not keywords:
        return []
    qs = Story.objects.select_related("user", "category")
    if category:
        qs = qs.filter(category__slug=category)
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    qs = qs.filter(_build_or_q(keywords, ("title", "content"))).distinct()

    # candidate ids 미리 추출 → engagement 카운트 한 번에 prefetch
    candidates = list(qs)
    cand_ids = [s.id for s in candidates]
    like_counts = dict(
        Like.objects.filter(target_type="story", target_id__in=cand_ids)
        .values_list("target_id")
        .annotate(c=Count("*"))
        .values_list("target_id", "c")
    )
    comment_counts = dict(
        Comment.objects.filter(story_id__in=cand_ids)
        .values_list("story_id")
        .annotate(c=Count("*"))
        .values_list("story_id", "c")
    )

    scored: list[Story] = []
    for s in candidates:
        matched = [kw for kw in keywords if _kw_in_any(kw, s.title, s.content)]
        like_n = like_counts.get(s.id, 0)
        comment_n = comment_counts.get(s.id, 0)
        composite = (
            len(matched) * 3.0
            + math.log10((s.view_count or 0) + 1)
            + 0.5 * like_n
            + 1.0 * comment_n
        )
        s._matched_keywords = matched
        s._score = len(matched)        # 표시용 (UI에 매칭 키워드 개수)
        s._composite_score = composite # 정렬용 (engagement 가중)
        s._engagement = {"likes": like_n, "comments": comment_n, "views": s.view_count}
        scored.append(s)
    scored.sort(key=lambda s: (s._composite_score, s.view_count), reverse=True)
    return scored[:limit]
