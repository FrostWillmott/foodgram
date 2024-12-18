from io import BytesIO

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from djoser.views import UserViewSet
from recipes.models import RecipeIngredient
from recipes.models import Tag, Recipe, Ingredient
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny, \
    IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from shopping_lists.models import ShoppingCart
from subscriptions.models import Subscription
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
from django.http import HttpResponse

from .permissions import IsAuthorOrReadOnly
from .serializers import CustomUserSerializer, SubscriptionSerializer, \
    AvatarSerializer, TagSerializer, IngredientSerializer, \
    RecipeWriteSerializer, RecipeReadSerializer, UserWithRecipesSerializer, \
    RecipeMinifiedSerializer

User = get_user_model()

pdfmetrics.registerFont(TTFont('DejaVuSans', 'api/v1/DejaVuSans.ttf'))

class FoodgramPagination(PageNumberPagination):
    """ Custom pagination class for Foodgram. """
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100

class CustomUserViewSet(UserViewSet):
    """ Custom view set for user-related actions. """
    serializer_class = CustomUserSerializer
    pagination_class = FoodgramPagination
    add_serializer = SubscriptionSerializer
    link_model = Subscription

    @action(methods=('get',), detail=False, permission_classes=(IsAuthenticated,), url_path='me', url_name='me')
    def me(self, request):
        """ Retrieve the authenticated user's details. """
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=('put',), detail=False, permission_classes=(IsAuthenticated,), serializer_class=AvatarSerializer, url_path='me/avatar', url_name='avatar')
    def avatar(self, request):
        """ Update the authenticated user's avatar. """
        user = request.user
        serializer = self.get_serializer(user, data=request.data, context={'request': request})
        if 'avatar' not in request.data:
            return Response({'error': 'Avatar field is required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            serializer.save()
            return Response({'avatar': serializer.data['avatar']}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @avatar.mapping.delete
    def delete_avatar(self, request: Request, *args, **kwargs):
        """ Delete the authenticated user's avatar. """
        user = self.request.user
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated], url_path='subscriptions')
    def subscriptions(self, request):
        """ Retrieve the list of users the authenticated user is subscribed to. """
        subscriptions = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = UserWithRecipesSerializer(page, many=True, context={
                'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = UserWithRecipesSerializer(subscriptions, many=True,
                                               context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated], url_path='subscribe')
    def subscribe(self, request, id=None):
        """ Subscribe the authenticated user to another user. """
        author = get_object_or_404(User, id=id)
        if request.user == author:
            return Response({"detail": "Cannot subscribe to yourself."},
                            status=status.HTTP_400_BAD_REQUEST)
        if Subscription.objects.filter(user=request.user,
                                       author=author).exists():
            return Response({"detail": "Already subscribed."},
                            status=status.HTTP_400_BAD_REQUEST)

        Subscription.objects.create(user=request.user, author=author)
        serializer = UserWithRecipesSerializer(author,
                                               context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """ Unsubscribe the authenticated user from another user. """
        author = get_object_or_404(User, id=id)
        subscription = Subscription.objects.filter(user=request.user,
                                                   author=author).first()
        if subscription is None:
            return Response({"detail": "Not subscribed."},
                            status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TagViewSet(ReadOnlyModelViewSet):
    """ View set for retrieving tags. """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)

    def list(self, request, *args, **kwargs):
        """ List all tags. """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class RecipeViewSet(ModelViewSet):
    """ View set for managing recipes. """
    queryset = Recipe.objects.all()
    pagination_class = FoodgramPagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = [SearchFilter]
    search_fields = ['tags__slug', 'author__id', 'is_favorited', 'is_in_shopping_cart']

    def get_serializer_class(self):
        """ Return the appropriate serializer class based on the request method. """
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def get_queryset(self):
        """ Return the filtered queryset based on query parameters. """
        queryset = super().get_queryset()
        user = self.request.user
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        tags = self.request.query_params.getlist('tags')
        author = self.request.query_params.get('author')

        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        if not user.is_authenticated:
            if author:
                queryset = queryset.filter(author__id=author)
            if is_favorited == '1' or is_in_shopping_cart == '1':
                return queryset.none()
            return queryset.order_by('-pub_date')

        if author:
            queryset = queryset.filter(author__id=author)

        if is_favorited == '1':
            queryset = queryset.filter(favorites__user=user)
        elif is_favorited == '0':
            queryset = queryset.exclude(favorites__user=user)

        if is_in_shopping_cart == '1':
            queryset = queryset.filter(in_carts__user=user)
        elif is_in_shopping_cart == '0':
            queryset = queryset.exclude(in_carts__user=user)

        return queryset.order_by('-pub_date')

    def perform_create(self, serializer):
        """ Save the new recipe and serialize the response data. """
        recipe = serializer.save(author=self.request.user)
        read_serializer = RecipeReadSerializer(recipe, context={
            'request': self.request})
        self.response_data = read_serializer.data

    def create(self, request, *args, **kwargs):
        """ Handle the creation of a new recipe. """
        response = super().create(request, *args, **kwargs)
        response.data = self.response_data
        return response

    def update(self, request, *args, **kwargs):
        """ Handle the update of an existing recipe. """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        read_serializer = RecipeReadSerializer(recipe,
                                               context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_recipe_link(self, request, pk=None):
        """ Generate a short link for the recipe. """
        short_link = f"https://kittygram.biz/recipes/{pk}"
        return Response({'short-link': short_link})

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """ Add a recipe to the authenticated user's favorites. """
        recipe = get_object_or_404(Recipe, pk=pk)
        if recipe.favorites.filter(user=request.user).exists():
            return Response({"detail": "Recipe already in favorites."},
                            status=status.HTTP_400_BAD_REQUEST)
        recipe.favorites.create(user=request.user)
        serializer = RecipeMinifiedSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def unfavorite(self, request, pk=None):
        """ Remove a recipe from the authenticated user's favorites. """
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = recipe.favorites.filter(user=request.user).first()
        if not favorite:
            return Response({"detail": "Recipe not in favorites."},
                            status=status.HTTP_400_BAD_REQUEST)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated], url_path='shopping_cart')
    def add_to_shopping_cart(self, request, pk=None):
        """ Add a recipe to the authenticated user's shopping cart. """
        recipe = get_object_or_404(Recipe, pk=pk)
        if ShoppingCart.objects.filter(user=request.user,
                                       recipe=recipe).exists():
            return Response({"detail": "Recipe already in shopping cart."},
                            status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeMinifiedSerializer(recipe,
                                              context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        """ Remove a recipe from the authenticated user's shopping cart. """
        recipe = get_object_or_404(Recipe, pk=pk)
        cart_item = ShoppingCart.objects.filter(user=request.user,
                                                recipe=recipe).first()
        if cart_item is None:
            return Response({"detail": "Recipe not in shopping cart."},
                            status=status.HTTP_400_BAD_REQUEST)
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Generate a PDF of the authenticated user's shopping cart."""
        cart_items = ShoppingCart.objects.filter(user=request.user)

        ingredients_map = {}
        for item in cart_items:
            recipe = item.recipe
            for ri in RecipeIngredient.objects.filter(recipe=recipe):
                name = ri.ingredient.name
                unit = ri.ingredient.measurement_unit
                amount = ri.amount
                if name not in ingredients_map:
                    ingredients_map[name] = {'unit': unit, 'amount': amount}
                else:
                    ingredients_map[name]['amount'] += amount

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)

        p.setFont("DejaVuSans", 14)
        p.drawString(100, 800, "Shopping List")
        p.setFont("DejaVuSans", 12)

        y = 780
        for name, data in ingredients_map.items():
            line = f"{name} - {data['amount']} {data['unit']}"
            p.drawString(100, y, line)
            y -= 20
            if y < 50:
                p.showPage()
                p.setFont("DejaVuSans", 12)
                y = 780

        p.showPage()
        p.save()

        buffer.seek(0)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.pdf"'
        response.write(buffer.read())
        return response

class IngredientViewSet(ReadOnlyModelViewSet):
    """View set for retrieving ingredients."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)

    def list(self, request, *args, **kwargs):
        """ List all ingredients or filter by name. """
        name = request.query_params.get('name', None)
        if name:
            queryset = self.get_queryset().filter(name__istartswith=name)
        else:
            queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
