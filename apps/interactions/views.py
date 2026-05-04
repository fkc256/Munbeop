from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.legal_data.models import Law, Precedent
from apps.stories.models import Story

from .models import Bookmark, Comment, Like, Report
from .permissions import IsCommentOwnerOrReadOnly
from .serializers import (
    BEST_LIKE_THRESHOLD,
    BookmarkListSerializer,
    BookmarkToggleSerializer,
    CommentCreateSerializer,
    CommentSerializer,
    CommentUpdateSerializer,
    LikeToggleSerializer,
    ReportCreateSerializer,
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
        # 최상위 댓글 노출 정책:
        # - 활성 댓글 → 항상 노출
        # - 작성자 직접 삭제(deletion_reason='author') → 활성 대댓글 ≥1일 때만 placeholder
        # - 신고/관리자 삭제(deletion_reason in ['report','admin']) → 자식 유무 무관 항상 placeholder
        #   (커뮤니티 운영 흔적은 가시화 — 펨코/디시 표준)
        active_top_ids = list(
            Comment.objects.filter(story=story, parent__isnull=True)
            .values_list("id", flat=True)
        )
        report_admin_deleted_ids = list(
            Comment.all_objects.filter(
                story=story, parent__isnull=True, is_deleted=True,
                deletion_reason__in=["report", "admin"],
            ).values_list("id", flat=True)
        )
        author_deleted_with_replies_ids = list(
            Comment.all_objects.filter(
                story=story, parent__isnull=True, is_deleted=True,
                deletion_reason="author",
            )
            .annotate(_alive_replies=Count("replies", filter=Q(replies__is_deleted=False)))
            .filter(_alive_replies__gt=0)
            .values_list("id", flat=True)
        )
        top_ids = active_top_ids + report_admin_deleted_ids + author_deleted_with_replies_ids

        # 정렬 옵션: ?ordering=best | latest | oldest (기본 best — 베스트 우선 + 그 외 최신순)
        ordering = request.query_params.get("ordering", "best")

        # 베스트 댓글: 활성 + 좋아요 ≥ 임계값. 별도 섹션으로 분리 응답
        if ordering == "best":
            # 좋아요 카운트 annotate
            qs_with_likes = Comment.all_objects.filter(id__in=top_ids).annotate(
                _like_count=Count(
                    "id",
                    filter=Q(
                        id__in=Like.objects.filter(target_type="comment").values("target_id")
                    ),
                )
            )
            # 위 annotate가 단순 boolean이라 정확 카운트는 별도 dict
            like_counts = dict(
                Like.objects.filter(target_type="comment", target_id__in=top_ids)
                .values_list("target_id")
                .annotate(c=Count("*"))
                .values_list("target_id", "c")
            )
            best_ids = [
                cid for cid in top_ids
                if like_counts.get(cid, 0) >= BEST_LIKE_THRESHOLD
            ]
            best_qs = (
                Comment.all_objects.filter(id__in=best_ids, is_deleted=False)
                .select_related("user", "story")
                .prefetch_related("replies__user")
            )
            # 베스트는 좋아요 수 desc, 동점이면 최신순
            best_list = sorted(
                list(best_qs),
                key=lambda c: (like_counts.get(c.id, 0), c.created_at),
                reverse=True,
            )
            # 일반 댓글 (베스트 제외, 베스트라도 deleted 여부 무관 — best_ids는 활성만이라 안전)
            normal_ids = [cid for cid in top_ids if cid not in set(best_ids)]
            normal_qs = (
                Comment.all_objects.filter(id__in=normal_ids)
                .select_related("user", "story")
                .prefetch_related("replies__user")
                .order_by("-created_at")
            )
            page = self.paginate_queryset(normal_qs)
            ser_normal = CommentSerializer(page, many=True, context={"request": request})
            ser_best = CommentSerializer(best_list, many=True, context={"request": request})
            paginated = self.get_paginated_response(ser_normal.data)
            paginated.data["best"] = ser_best.data
            return paginated

        # 단순 정렬: latest / oldest
        order_field = "-created_at" if ordering == "latest" else "created_at"
        qs = (
            Comment.all_objects.filter(id__in=top_ids)
            .select_related("user", "story")
            .prefetch_related("replies__user")
            .order_by(order_field)
        )
        page = self.paginate_queryset(qs)
        ser = CommentSerializer(page, many=True, context={"request": request})
        paginated = self.get_paginated_response(ser.data)
        paginated.data["best"] = []
        return paginated

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


class CommentReportView(APIView):
    """POST /api/comments/<pk>/report/

    같은 사용자의 같은 댓글 중복 신고 X.
    임계값(Report.REPORT_THRESHOLD) 누적 시 자동 soft delete (deletion_reason='report').
    """

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        comment = get_object_or_404(Comment.objects, pk=pk)
        if comment.user_id == request.user.id:
            raise PermissionDenied("자신의 댓글은 신고할 수 없습니다.")

        ser = ReportCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        report, created = Report.objects.get_or_create(
            user=request.user,
            comment=comment,
            defaults={
                "reason": ser.validated_data["reason"],
                "detail": ser.validated_data.get("detail", ""),
            },
        )
        if not created:
            return Response(
                {"detail": "이미 신고한 댓글입니다.", "report_count": comment.reports.count()},
                status=status.HTTP_200_OK,
            )

        report_count = comment.reports.count()
        auto_deleted = False
        if report_count >= Report.REPORT_THRESHOLD and not comment.is_deleted:
            comment.soft_delete(reason="report")
            auto_deleted = True

        return Response(
            {
                "detail": "신고 접수됨",
                "report_count": report_count,
                "auto_deleted": auto_deleted,
            },
            status=status.HTTP_201_CREATED,
        )


class MyBookmarksView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = BookmarkListSerializer

    def get_queryset(self):
        qs = Bookmark.objects.filter(user=self.request.user)
        target_type = self.request.query_params.get("target_type")
        if target_type:
            qs = qs.filter(target_type=target_type)
        return qs
