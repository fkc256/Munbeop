from django.urls import path

from .views import (
    BookmarkToggleView,
    CommentDetailView,
    LikeToggleView,
    MyBookmarksView,
    StoryCommentListCreateView,
)

app_name = "interactions"

urlpatterns = [
    path(
        "stories/<int:story_pk>/comments/",
        StoryCommentListCreateView.as_view(),
        name="story-comment-list-create",
    ),
    path("comments/<int:pk>/", CommentDetailView.as_view(), name="comment-detail"),
    path("likes/toggle/", LikeToggleView.as_view(), name="like-toggle"),
    path("bookmarks/toggle/", BookmarkToggleView.as_view(), name="bookmark-toggle"),
    path("bookmarks/", MyBookmarksView.as_view(), name="my-bookmarks"),
]
