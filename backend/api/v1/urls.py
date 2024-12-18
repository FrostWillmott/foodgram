from django.conf.urls.static import static
from django.urls import include, path
from foodgram_backend.settings import MEDIA_ROOT, MEDIA_URL
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
)

router = DefaultRouter()
router.register(r"users", CustomUserViewSet, basename="users")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"recipes", RecipeViewSet, basename="recipe")
router.register(r"ingredients", IngredientViewSet, basename="ingredient")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
    path("auth/login/", include("django.contrib.auth.urls")),
] + static(MEDIA_URL, document_root=MEDIA_ROOT)
