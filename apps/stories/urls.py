from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, StoryViewSet

router = DefaultRouter()
router.register(r"stories", StoryViewSet, basename="story")
router.register(r"categories", CategoryViewSet, basename="category")

app_name = "stories"
urlpatterns = router.urls
