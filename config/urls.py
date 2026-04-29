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
    # Pages (STEP 6A)
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("signup/", TemplateView.as_view(template_name="pages/signup.html"), name="signup-page"),
    path("login/", TemplateView.as_view(template_name="pages/login.html"), name="login-page"),
]
