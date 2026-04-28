from django.db.models import (
    Count,
    Exists,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Value,
)
from django.db.models.functions import Coalesce
from rest_framework import filters, permissions, viewsets
from rest_framework.response import Response

from .models import Category, Story
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    CategorySerializer,
    StoryCreateUpdateSerializer,
    StoryDetailSerializer,
    StoryListSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class StoryViewSet(viewsets.ModelViewSet):
    permission_classes = (IsOwnerOrReadOnly,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ("created_at", "view_count")
    ordering = ("-created_at",)

    def get_queryset(self):
        qs = Story.objects.select_related("user", "category")
        category_slug = self.request.query_params.get("category")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        # N+1 방지: 댓글/좋아요 카운트, 인증 시 좋아요/북마크 여부 annotate
        from apps.interactions.models import Bookmark, Like

        like_count_sq = (
            Like.objects.filter(target_type="story", target_id=OuterRef("pk"))
            .order_by()
            .values("target_id")
            .annotate(c=Count("*"))
            .values("c")
        )
        qs = qs.annotate(
            _comment_count=Count(
                "comments", filter=Q(comments__is_deleted=False), distinct=True
            ),
            _like_count=Coalesce(
                Subquery(like_count_sq, output_field=IntegerField()),
                Value(0),
                output_field=IntegerField(),
            ),
        )
        user = self.request.user
        if user.is_authenticated:
            is_liked_sq = Like.objects.filter(
                user=user, target_type="story", target_id=OuterRef("pk")
            )
            is_bookmarked_sq = Bookmark.objects.filter(
                user=user, target_type="story", target_id=OuterRef("pk")
            )
            qs = qs.annotate(
                _is_liked=Exists(is_liked_sq),
                _is_bookmarked=Exists(is_bookmarked_sq),
            )
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return StoryListSerializer
        if self.action == "retrieve":
            return StoryDetailSerializer
        return StoryCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # create 직후 detail 응답: 새로 생성된 객체에 annotate 다시 적용
        instance = self.get_queryset().get(pk=serializer.instance.pk)
        out = StoryDetailSerializer(instance, context=self.get_serializer_context())
        return Response(out.data, status=201)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance = self.get_queryset().get(pk=serializer.instance.pk)
        out = StoryDetailSerializer(instance, context=self.get_serializer_context())
        return Response(out.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Story.objects.filter(pk=instance.pk).update(view_count=F("view_count") + 1)
        # view_count 증가 + annotate 재계산을 위해 queryset에서 다시 조회
        fresh = self.get_queryset().get(pk=instance.pk)
        serializer = self.get_serializer(fresh)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=204)
