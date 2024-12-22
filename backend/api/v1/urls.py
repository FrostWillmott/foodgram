from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from foodgram_backend.settings import MEDIA_ROOT, MEDIA_URL
from .views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    UserViewSet
)


router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("tags", TagViewSet, basename="tag")
router.register("recipes", RecipeViewSet, basename="recipe")
router.register("ingredients", IngredientViewSet, basename="ingredient")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
    path("auth/login/", include("django.contrib.auth.urls")),
] + static(MEDIA_URL, document_root=MEDIA_ROOT)