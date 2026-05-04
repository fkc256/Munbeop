from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SearchQuery
from .serializers import (
    LawSearchResultSerializer,
    PrecedentSearchResultSerializer,
    StorySearchResultSerializer,
)
from .services import search_laws, search_precedents, search_stories
from .utils import extract_keywords


DISCLAIMER = (
    "본 검색 결과는 법률 정보 제공 목적이며, 법률 자문이 아닙니다. "
    "구체적인 법률 자문은 변호사와 상담하시기 바랍니다."
)


class TrendingSearchView(APIView):
    """실시간 검색어 랭킹 (펨코 스타일).

    GET /api/search/trending/?hours=24&limit=10
    - hours: 집계 기간 (시간 단위, 기본 24)
    - limit: 상위 N개 (기본 10, 최대 50)
    """

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        try:
            hours = int(request.query_params.get("hours", 24))
            limit = min(int(request.query_params.get("limit", 10)), 50)
        except (TypeError, ValueError):
            hours, limit = 24, 10
        since = timezone.now() - timedelta(hours=hours)

        rows = (
            SearchQuery.objects.filter(created_at__gte=since)
            .values("query")
            .annotate(count=Count("id"))
            .order_by("-count", "-query")[:limit]
        )
        items = [
            {"rank": idx + 1, "query": r["query"], "count": r["count"]}
            for idx, r in enumerate(rows)
        ]
        return Response({
            "hours": hours,
            "since": since.isoformat(),
            "items": items,
        })


class PopularStoriesView(APIView):
    """포텐 (인기글) 랭킹.

    GET /api/stories/popular/?days=7&limit=10
    - 점수 = log10(view+1)*2 + like*3 + comment*5
    - 임계 (15점) 넘으면 포텐 (is_hot=true)
    """

    permission_classes = (permissions.AllowAny,)
    HOT_THRESHOLD = 15.0

    def get(self, request):
        import math

        from apps.interactions.models import Comment, Like
        from apps.stories.models import Story

        try:
            days = int(request.query_params.get("days", 7))
            limit = min(int(request.query_params.get("limit", 10)), 50)
        except (TypeError, ValueError):
            days, limit = 7, 10
        since = timezone.now() - timedelta(days=days)

        qs = Story.objects.filter(created_at__gte=since).select_related("category", "user")
        candidates = list(qs)
        if not candidates:
            # 시연 데이터셋이 모두 며칠 전이면 days 무시하고 전체에서 score 기반
            candidates = list(Story.objects.select_related("category", "user"))

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

        scored = []
        for s in candidates:
            like_n = like_counts.get(s.id, 0)
            comment_n = comment_counts.get(s.id, 0)
            score = (
                math.log10((s.view_count or 0) + 1) * 2
                + like_n * 3
                + comment_n * 5
            )
            scored.append((s, score, like_n, comment_n))
        scored.sort(key=lambda x: x[1], reverse=True)
        scored = scored[:limit]

        items = []
        for rank, (s, score, like_n, comment_n) in enumerate(scored, start=1):
            cat = s.category.slug if s.category else None
            items.append({
                "rank": rank,
                "id": s.id,
                "title": s.title,
                "category": cat,
                "view_count": s.view_count,
                "like_count": like_n,
                "comment_count": comment_n,
                "score": round(score, 2),
                "is_hot": score >= self.HOT_THRESHOLD,
            })
        return Response({
            "days": days,
            "since": since.isoformat(),
            "hot_threshold": self.HOT_THRESHOLD,
            "items": items,
        })


def _coerce_int(value) -> int | None:
    if value in (None, "", "null"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class UnifiedSearchView(APIView):
    """통합 검색 — 사연 한 줄 입력 → 법령 / 판례 / 유사 사연 한 번에."""

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        return self._search(
            query=request.data.get("query", ""),
            category=request.data.get("category"),
            exclude_story_id=request.data.get("exclude_story_id"),
            boost_category=request.data.get("boost_category"),
        )

    def get(self, request):
        return self._search(
            query=request.query_params.get("q", ""),
            category=request.query_params.get("category"),
            exclude_story_id=request.query_params.get("exclude_story_id"),
            boost_category=request.query_params.get("boost_category"),
        )

    def _search(self, query: str, category: str | None, exclude_story_id,
                boost_category: str | None = None):
        query = query or ""
        category = category or None
        boost_category = boost_category or None
        exclude_id = _coerce_int(exclude_story_id)

        keywords = extract_keywords(query)
        empty_results = {"laws": [], "precedents": [], "stories": []}

        # 검색 로그 저장 (실시간 검색어 랭킹용)
        if query.strip() and keywords:
            user = self.request.user if self.request.user.is_authenticated else None
            SearchQuery.objects.create(
                query=query.strip()[:500],
                keywords=",".join(keywords)[:500],
                user=user,
                category=(category or "")[:20],
            )

        if not keywords:
            return Response(
                {
                    "query": query,
                    "extracted_keywords": [],
                    "results": empty_results,
                    "counts": {"laws": 0, "precedents": 0, "stories": 0},
                    "disclaimer": DISCLAIMER,
                }
            )

        laws = search_laws(keywords, category=category)
        precedents = search_precedents(keywords, category=category)
        stories = search_stories(
            keywords, category=category, exclude_id=exclude_id,
            boost_category=boost_category,
        )

        ctx = {"request": self.request}
        return Response(
            {
                "query": query,
                "extracted_keywords": keywords,
                "results": {
                    "laws": LawSearchResultSerializer(laws, many=True, context=ctx).data,
                    "precedents": PrecedentSearchResultSerializer(
                        precedents, many=True, context=ctx
                    ).data,
                    "stories": StorySearchResultSerializer(
                        stories, many=True, context=ctx
                    ).data,
                },
                "counts": {
                    "laws": len(laws),
                    "precedents": len(precedents),
                    "stories": len(stories),
                },
                "disclaimer": DISCLAIMER,
            }
        )
