from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.legal_data.models import Law, Precedent
from apps.stories.models import Story

from .models import Bookmark, Comment, Like
from .permissions import IsCommentOwnerOrReadOnly
from .serializers import (
    BookmarkListSerializer,
    BookmarkToggleSerializer,
    CommentCreateSerializer,
    CommentSerializer,
    CommentUpdateSerializer,
    LikeToggleSerializer,
)


class StoryCommentListCreateView(generics.GenericAPIView):
    """GET /api/stories/<story_pk>/comments/  : 최상위 댓글 목록 (페이지네이션, replies nested)
    POST /api/stories/<story_pk>/comments/    : 댓글/대댓글 작성 (인증 필요)
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def _get_story(self):
        return get_object_or_404(Story.objects, pk=self.kwargs["story_pk"])

    def get(self, request, *args, **kwargs):
        story = self._get_story()
        # 최상위 댓글: 활성이거나(deleted여도 활성 대댓글 ≥1)
        active_top = Comment.objects.filter(story=story, parent__isnull=True)
        deleted_with_replies = (
            Comment.all_objects.filter(
                story=story, parent__isnull=True, is_deleted=True
            )
            .annotate(_alive_replies=Count("replies", filter=Q(replies__is_deleted=False)))
            .filter(_alive_replies__gt=0)
        )
        # union 후 created_at asc 정렬
        top_ids = list(active_top.values_list("id", flat=True)) + list(
            deleted_with_replies.values_list("id", flat=True)
        )
        qs = (
            Comment.all_objects.filter(id__in=top_ids)
            .select_related("user")
            .prefetch_related("replies__user")
            .order_by("created_at")
        )
        page = self.paginate_queryset(qs)
        ser = CommentSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)

    def post(self, request, *args, **kwargs):
        story = self._get_story()
        ser = CommentCreateSerializer(
            data=request.data, context={"request": request, "story": story}
        )
        ser.is_valid(raise_exception=True)
        comment = Comment.objects.create(
            user=request.user,
            story=story,
            parent=ser.validated_data.get("parent"),
            content=ser.validated_data["content"],
        )
        out = CommentSerializer(comment, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)


class CommentDetailView(generics.GenericAPIView):
    """GET/PATCH/DELETE /api/comments/<pk>/."""

    permission_classes = (IsCommentOwnerOrReadOnly,)
    serializer_class = CommentSerializer

    def get_object(self):
        # 활성만 (soft-deleted는 직접 조회 시 404)
        obj = get_object_or_404(Comment.objects, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return Response(CommentSerializer(obj, context={"request": request}).data)

    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        ser = CommentUpdateSerializer(obj, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(CommentSerializer(obj, context={"request": request}).data)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _get_like_target_or_404(target_type: str, target_id: int):
    if target_type == "story":
        return get_object_or_404(Story.objects, pk=target_id)
    if target_type == "comment":
        return get_object_or_404(Comment.objects, pk=target_id)
    raise NotFound()


def _get_bookmark_target_or_404(target_type: str, target_id: int):
    if target_type == "story":
        return get_object_or_404(Story.objects, pk=target_id)
    if target_type == "law":
        return get_object_or_404(Law.objects.filter(is_active=True), pk=target_id)
    if target_type == "precedent":
        return get_object_or_404(Precedent.objects, pk=target_id)
    raise NotFound()


class LikeToggleView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        ser = LikeToggleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        target_type = ser.validated_data["target_type"]
        target_id = ser.validated_data["target_id"]

        _get_like_target_or_404(target_type, target_id)  # 404 if not exist

        existing = Like.objects.filter(
            user=request.user, target_type=target_type, target_id=target_id
        ).first()
        if existing:
            existing.delete()
            liked = False
        else:
            Like.objects.create(
                user=request.user, target_type=target_type, target_id=target_id
            )
            liked = True
        count = Like.objects.filter(
            target_type=target_type, target_id=target_id
        ).count()
        return Response({"liked": liked, "count": count})


class BookmarkToggleView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        ser = BookmarkToggleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        target_type = ser.validated_data["target_type"]
        target_id = ser.validated_data["target_id"]

        _get_bookmark_target_or_404(target_type, target_id)

        existing = Bookmark.objects.filter(
            user=request.user, target_type=target_type, target_id=target_id
        ).first()
        if existing:
            existing.delete()
            bookmarked = False
        else:
            Bookmark.objects.create(
                user=request.user, target_type=target_type, target_id=target_id
            )
            bookmarked = True
        return Response({"bookmarked": bookmarked})


class MyBookmarksView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = BookmarkListSerializer

    def get_queryset(self):
        qs = Bookmark.objects.filter(user=self.request.user)
        target_type = self.request.query_params.get("target_type")
        if target_type:
            qs = qs.filter(target_type=target_type)
        return qs
