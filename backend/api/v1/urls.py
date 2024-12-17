from django.conf.urls.static import static
from django.urls import path, include
from foodgram_backend.settings import MEDIA_URL, MEDIA_ROOT
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet, TagViewSet, RecipeViewSet, \
    IngredientViewSet

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
# router.register(r'recipes/(?P<recipe_id>\d+)/favorite', RecipeViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('auth/login/', include('django.contrib.auth.urls')),
] + static(MEDIA_URL, document_root=MEDIA_ROOT)