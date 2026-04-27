from django.db.models import F
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
        out = StoryDetailSerializer(
            serializer.instance, context=self.get_serializer_context()
        )
        return Response(out.data, status=201)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        out = StoryDetailSerializer(
            serializer.instance, context=self.get_serializer_context()
        )
        return Response(out.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Story.objects.filter(pk=instance.pk).update(view_count=F("view_count") + 1)
        instance.refresh_from_db(fields=["view_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=204)
