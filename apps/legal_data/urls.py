from rest_framework.routers import DefaultRouter

from .views import LawViewSet, PrecedentViewSet

router = DefaultRouter()
router.register(r"laws", LawViewSet, basename="law")
router.register(r"precedents", PrecedentViewSet, basename="precedent")

app_name = "legal_data"
urlpatterns = router.urls
