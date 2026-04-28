from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("api/", include("apps.stories.urls", namespace="stories")),
    path("api/", include("apps.legal_data.urls", namespace="legal_data")),
]
