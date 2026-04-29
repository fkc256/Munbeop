from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    # API
    path("api/accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("api/", include("apps.stories.urls", namespace="stories")),
    path("api/", include("apps.legal_data.urls", namespace="legal_data")),
    path("api/", include("apps.search.urls", namespace="search")),
    path("api/", include("apps.interactions.urls", namespace="interactions")),
    # Pages — 6A
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("signup/", TemplateView.as_view(template_name="pages/signup.html"), name="signup-page"),
    path("login/", TemplateView.as_view(template_name="pages/login.html"), name="login-page"),
    # Pages — 6B (사연/검색/법령/판례/마이페이지)
    path("stories/", TemplateView.as_view(template_name="pages/story_list.html"), name="story-list-page"),
    path("stories/new/", TemplateView.as_view(template_name="pages/story_form.html"), name="story-new-page"),
    path("stories/<int:pk>/", TemplateView.as_view(template_name="pages/story_detail.html"), name="story-detail-page"),
    path("stories/<int:pk>/edit/", TemplateView.as_view(template_name="pages/story_form.html"), name="story-edit-page"),
    path("laws/", TemplateView.as_view(template_name="pages/law_list.html"), name="law-list-page"),
    path("laws/<int:pk>/", TemplateView.as_view(template_name="pages/law_detail.html"), name="law-detail-page"),
    path("precedents/", TemplateView.as_view(template_name="pages/precedent_list.html"), name="precedent-list-page"),
    path("precedents/<int:pk>/", TemplateView.as_view(template_name="pages/precedent_detail.html"), name="precedent-detail-page"),
    path("search/", TemplateView.as_view(template_name="pages/search_result.html"), name="search-page"),
    path("me/", TemplateView.as_view(template_name="pages/my_page.html"), name="my-page"),
]
