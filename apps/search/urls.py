from django.urls import path

from .views import PopularStoriesView, TrendingSearchView, UnifiedSearchView

app_name = "search"
urlpatterns = [
    path("search/", UnifiedSearchView.as_view(), name="unified-search"),
    path("search/trending/", TrendingSearchView.as_view(), name="trending"),
    path("search/popular/", PopularStoriesView.as_view(), name="popular-stories"),
]
