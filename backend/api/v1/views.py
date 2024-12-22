import logging
import os
from io import BytesIO

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from foodgram_backend import settings
from recipes.models import Ingredient, Recipe, Tag
from shopping_lists.models import ShoppingCart
from subscriptions.models import Subscription
from .filters import IngredientFilter, RecipeFilter
from .pagination import FoodgramPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)

User = get_user_model()

font_path = os.path.join(settings.BASE_DIR, "api", "v1", "DejaVuSans.ttf")
pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

logger = logging.getLogger(__name__)

def shortlink_redirect_view(request, short_link):
    logger.debug(f"Received short link: {short_link}")
    recipe = get_object_or_404(Recipe, short_link=short_link)
    logger.debug(f"Redirecting to recipe ID: {recipe.id}")
    return redirect(f"/recipes/{recipe.id}/")


class UserViewSet(UserViewSet):
    """View set for user-related actions."""

    serializer_class = UserSerializer
    pagination_class = FoodgramPagination

    @action(
        methods=("get",),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path="me",
        url_name="me",
    )
    def me(self, request):
        """Retrieve the authenticated user's details."""
        return super().me(request)

    @action(
        methods=("put",),
        detail=False,
        permission_classes=(IsAuthenticated,),
        serializer_class=AvatarSerializer,
        url_path="me/avatar",
        url_name="avatar",
    )
    def avatar(self, request):
        """Update the authenticated user's avatar."""
        user = request.user
        serializer = self.get_serializer(
            user,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"avatar": serializer.data["avatar"]},
            status=status.HTTP_200_OK,
        )

    @avatar.mapping.delete
    def delete_avatar(self, request: Request, *args, **kwargs):
        """Delete the authenticated user's avatar."""
        user = self.request.user
        if user.avatar:
            user.avatar.delete(save=False)
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="subscriptions",
    )
    def subscriptions(self, request):
        """
        Retrieve the list of users the authenticated user is subscribed to.
        """
        subscriptions = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(subscriptions)
        serializer = UserWithRecipesSerializer(
            page,
            many=True,
            context={"request": request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, id=None):
        """Subscribe the authenticated user to another user."""
        author = get_object_or_404(User, id=id)
        serializer = SubscriptionSerializer(
            data={"user": request.user.id, "author": author.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Unsubscribe the authenticated user from another user."""
        author = get_object_or_404(User, id=id)
        deleted_count, _ = Subscription.objects.filter(
            user=request.user,
            author=author,
        ).delete()
        if not deleted_count:
            return Response(
                {"detail": "Not subscribed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    """View set for retrieving tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipeViewSet(ModelViewSet):
    """View set for managing recipes."""

    queryset = Recipe.objects.all()
    pagination_class = FoodgramPagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = RecipeFilter
    search_fields = [
        "tags__slug",
        "author__id",
        "is_favorited",
        "is_in_shopping_cart",
    ]

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the request method.
        """
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Add a recipe to the authenticated user's favorites."""
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = FavoriteSerializer(
            data={"recipe": recipe.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def unfavorite(self, request, pk=None):
        """Remove a recipe from the authenticated user's favorites."""
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted_count, _ = recipe.favorites.filter(user=request.user).delete()
        if not deleted_count:
            return Response(
                {"detail": "Recipe not in favorites."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="shopping_cart",
    )
    def add_to_shopping_cart(self, request, pk=None):
        """Add a recipe to the authenticated user's shopping cart."""
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = ShoppingCartSerializer(
            data={"recipe": recipe.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        """Remove a recipe from the authenticated user's shopping cart."""
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted_count, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted_count:
            return Response(
                {"detail": "Recipe not in shopping cart."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        """Generate a PDF of the authenticated user's shopping cart."""
        cart_items = (
            ShoppingCart.objects.filter(user=request.user)
            .values(
                "recipe__recipeingredient__ingredient__name",
                "recipe__recipeingredient__ingredient__measurement_unit",
            )
            .annotate(total_amount=Sum("recipe__recipeingredient__amount"))
        )

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)

        p.setFont("DejaVuSans", 14)
        p.drawString(100, 800, "Shopping List")
        p.setFont("DejaVuSans", 12)

        y = 780

        for item in cart_items:
            item_3 = "recipe__recipeingredient__ingredient__measurement_unit"
            line = (
                f"{item['recipe__recipeingredient__ingredient__name']} - "
                f"{item['total_amount']}"
                f"{item[item_3]}"
            )
            p.drawString(100, y, line)
            y -= 20
            if y < 50:
                p.showPage()
                p.setFont("DejaVuSans", 12)
                y = 780

        p.showPage()
        p.save()

        buffer.seek(0)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.pdf"'
        )
        response.write(buffer.read())
        return response

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_recipe_link(self, request, pk=None):
        """Generate a short link for the recipe."""
        recipe = self.get_object()
        short_link = f"https://kittygram.biz/{recipe.short_link}"
        return Response({"short-link": short_link})


class IngredientViewSet(ReadOnlyModelViewSet):
    """View set for retrieving ingredients."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
