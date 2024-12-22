from django.conf.urls.static import static
from django.shortcuts import redirect
from django.urls import include, path
from rest_framework.generics import get_object_or_404
from rest_framework.routers import DefaultRouter

from foodgram_backend.settings import MEDIA_ROOT, MEDIA_URL
from .views import (
    UserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
)
from recipes.models import Recipe


def shortlink_redirect_view(request, short_link):
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return redirect(f"/recipes/{recipe.id}/")


router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("tags", TagViewSet, basename="tag")
router.register("recipes", RecipeViewSet, basename="recipe")
router.register("ingredients", IngredientViewSet, basename="ingredient")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
    path("auth/login/", include("django.contrib.auth.urls")),
    path("<str:short_link>/", shortlink_redirect_view, name="recipe-shortlink"),
] + static(MEDIA_URL, document_root=MEDIA_ROOT)
