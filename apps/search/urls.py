from django.urls import path

from .views import UnifiedSearchView

app_name = "search"
urlpatterns = [
    path("search/", UnifiedSearchView.as_view(), name="unified-search"),
]
