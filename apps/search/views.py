from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

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
        )

    def get(self, request):
        return self._search(
            query=request.query_params.get("q", ""),
            category=request.query_params.get("category"),
            exclude_story_id=request.query_params.get("exclude_story_id"),
        )

    def _search(self, query: str, category: str | None, exclude_story_id):
        query = query or ""
        category = category or None
        exclude_id = _coerce_int(exclude_story_id)

        keywords = extract_keywords(query)
        empty_results = {"laws": [], "precedents": [], "stories": []}
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
        stories = search_stories(keywords, category=category, exclude_id=exclude_id)

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
