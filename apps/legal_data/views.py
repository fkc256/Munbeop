from django.db.models import Q
from rest_framework import filters, permissions, viewsets

from .models import Law, Precedent
from .serializers import (
    LawDetailSerializer,
    LawListSerializer,
    PrecedentDetailSerializer,
    PrecedentListSerializer,
)


class LawViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.AllowAny,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ("law_name", "article_number")
    ordering = ("law_name", "article_number")

    def get_queryset(self):
        qs = Law.objects.filter(is_active=True).select_related("category")
        params = self.request.query_params
        category = params.get("category")
        if category:
            qs = qs.filter(category__slug=category)
        keyword = params.get("keyword")
        if keyword:
            qs = qs.filter(
                Q(law_name__icontains=keyword)
                | Q(keywords__icontains=keyword)
                | Q(content__icontains=keyword)
            )
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LawDetailSerializer
        return LawListSerializer


class PrecedentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.AllowAny,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ("judgment_date", "court")
    ordering = ("-judgment_date",)

    def get_queryset(self):
        qs = Precedent.objects.select_related("category").prefetch_related(
            "related_laws"
        )
        params = self.request.query_params
        category = params.get("category")
        if category:
            qs = qs.filter(category__slug=category)
        court = params.get("court")
        if court:
            qs = qs.filter(court=court)
        result_type = params.get("result_type")
        if result_type:
            qs = qs.filter(result_type=result_type)
        keyword = params.get("keyword")
        if keyword:
            qs = qs.filter(
                Q(case_name__icontains=keyword)
                | Q(keywords__icontains=keyword)
                | Q(summary__icontains=keyword)
            )
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PrecedentDetailSerializer
        return PrecedentListSerializer
