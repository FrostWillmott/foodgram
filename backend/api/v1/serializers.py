from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField

from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    CharField,
    IntegerField,
    SerializerMethodField,
)
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from favorites.models import Favorite
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from shopping_lists.models import ShoppingCart
from subscriptions.models import Subscription

User = get_user_model()


class UserSerializer(UserSerializer):
    """Serializer for user model."""

    is_subscribed = SerializerMethodField()
    avatar = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
            "is_subscribed",
            "avatar",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def get_is_subscribed(self, obj):
        """Check if the authenticated user is subscribed to the given user."""
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user,
                author=obj,
            ).exists(),
        )

    def get_is_in_shopping_cart(self, obj):
        """Check if the recipe is in the authenticated user's shopping cart."""
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj,
            ).exists(),
        )

    def get_is_favorited(self, obj):
        """Check if the recipe is favorited by the authenticated user."""
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and obj.favorites.filter(user=request.user).exists(),
        )

    def get_recipes_count(self, obj):
        """Get the count of recipes authored by the given user."""
        return Recipe.objects.filter(author=obj).count()

    def get_avatar(self, obj):
        """Get the URL of the user's avatar."""
        if obj.avatar:
            return obj.avatar.url
        return None


class AvatarSerializer(ModelSerializer):
    """Serializer for user avatar."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ("avatar",)

    def validate_avatar(self, value):
        """Validate the avatar field."""
        if not value:
            raise ValidationError("Avatar field is required.")
        return value


class SubscriptionSerializer(ModelSerializer):
    """Serializer for creating and validating subscriptions."""

    class Meta:
        model = Subscription
        fields = ("user", "author")
        extra_kwargs = {
            "user": {"read_only": True},
            "author": {"required": True},
        }

    def validate(self, data):
        """Validate the subscription data."""
        user = self.context["request"].user
        author = data["author"]

        if user == author:
            raise ValidationError("Cannot subscribe to yourself.")

        if Subscription.objects.filter(user=user, author=author).exists():
            raise ValidationError("Already subscribed.")

        return data

    def create(self, validated_data):
        """Create a new subscription."""
        user = self.context["request"].user
        validated_data["user"] = user
        return super().create(validated_data)

    def to_representation(self, instance):
        """Return the subscription data in the desired format."""
        author_data = UserWithRecipesSerializer(
            instance.author,
            context=self.context,
        ).data
        return author_data


class UserWithRecipesSerializer(UserSerializer):
    """Serializer for users with their recipes."""

    is_subscribed = SerializerMethodField()
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()
    avatar = SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        """Check if the authenticated user is subscribed to the given user."""
        user = self.context["request"].user
        return Subscription.objects.filter(user=user, author=obj).exists()

    def get_recipes(self, obj):
        """Get the recipes authored by the given user."""
        recipes_limit = self.context["request"].query_params.get(
            "recipes_limit",
        )
        recipes = Recipe.objects.filter(author=obj)

        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except ValueError:
                pass
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Get the count of recipes authored by the given user."""
        return Recipe.objects.filter(author=obj).count()

    def get_avatar(self, obj):
        """Get the URL of the user's avatar."""
        if obj.avatar:
            return obj.avatar.url
        return None


class TagSerializer(ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class IngredientInRecipeReadSerializer(ModelSerializer):
    """Serializer for reading ingredients in a recipe."""

    id = IntegerField(source="ingredient.id")
    name = CharField(source="ingredient.name", read_only=True)
    measurement_unit = CharField(
        source="ingredient.measurement_unit",
        read_only=True,
    )
    amount = IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class IngredientInRecipeWriteSerializer(ModelSerializer):
    """Serializer for writing ingredients in a recipe."""

    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")

    def validate(self, data):
        """Validate the ingredient data."""
        if data["amount"] < 1:
            raise ValidationError("Ingredient amount must be at least 1.")
        try:
            Ingredient.objects.get(id=data["ingredient"].id)
        except Ingredient.DoesNotExist:
            raise ValidationError(
                f"Ingredient with id {data['ingredient'].id} does not exist.",
            )
        return data


class RecipeReadSerializer(ModelSerializer):
    """Serializer for reading recipes."""

    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    ingredients = IngredientInRecipeReadSerializer(
        many=True,
        source="recipeingredient_set",
    )
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        """Check if the recipe is favorited by the authenticated user."""
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Check if the recipe is in the authenticated user's shopping cart."""
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.in_carts.filter(user=user).exists()


class RecipeWriteSerializer(ModelSerializer):
    """Serializer for writing recipes."""

    ingredients = IngredientInRecipeWriteSerializer(many=True, write_only=True)
    image = Base64ImageField()
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = ("author",)

    def validate(self, data):
        """Validate the entire payload."""
        ingredients = data.get("ingredients")
        tags = data.get("tags")
        if not ingredients:
            raise ValidationError(
                {"ingredients": "Ingredients field cannot be empty."},
            )
        ingredient_ids = set()
        for ingredient_data in ingredients:
            ingredient_id = ingredient_data["ingredient"].id
            if ingredient_id in ingredient_ids:
                raise ValidationError(
                    {
                        "ingredients": "Duplicate ingredients are not allowed.",
                    },
                )
            ingredient_ids.add(ingredient_id)
        if not tags:
            raise ValidationError({"tags": "Tags field cannot be empty."})
        if len(tags) != len(set(tags)):
            raise ValidationError({"tags": "Duplicate tags are not allowed."})

        return data

    def validate_image(self, value):
        """Validate the image field."""
        if not value:
            raise ValidationError("Image field cannot be empty.")
        return value

    def _create_recipe_ingredients(self, recipe, ingredients_data):
        """Create RecipeIngredient instances for the given recipe."""
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data["ingredient"],
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        """Create a new recipe."""
        ingredients_data = validated_data.pop("ingredients")
        tags = validated_data.pop("tags", [])
        recipe = Recipe.objects.create(
            author=self.context["request"].user,
            **validated_data,
        )
        recipe.tags.set(tags)

        self._create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Update an existing recipe."""
        ingredients_data = validated_data.pop("ingredients", None)
        tags = validated_data.pop("tags", None)

        if ingredients_data is None or len(ingredients_data) == 0:
            raise ValidationError(
                {"ingredients": "This field cannot be empty or missing."},
            )

        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.ingredients.clear()

        self._create_recipe_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        """Return the recipe data in the desired format."""
        read_serializer = RecipeReadSerializer(instance, context=self.context)
        return read_serializer.data


class IngredientSerializer(ModelSerializer):
    """Serializer for ingredients."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeMinifiedSerializer(ModelSerializer):
    """Serializer for a minified version of recipes."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FavoriteSerializer(ModelSerializer):
    class Meta:
        model = Favorite
        fields = ("user", "recipe")
        extra_kwargs = {
            "user": {"read_only": True},
            "recipe": {"required": True},
        }

    def validate(self, data):
        user = self.context["request"].user
        recipe = data["recipe"]

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError("Recipe is already in favorites.")

        return data

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["user"] = user
        return super().create(validated_data)

    def to_representation(self, instance):
        recipe_data = RecipeMinifiedSerializer(
            instance.recipe,
            context=self.context,
        ).data
        return recipe_data


class ShoppingCartSerializer(ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ("user", "recipe")
        extra_kwargs = {
            "user": {"read_only": True},
            "recipe": {"required": True},
        }

    def validate(self, data):
        user = self.context["request"].user
        recipe = data["recipe"]

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError("Recipe is already in shopping cart.")

        return data

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["user"] = user
        return super().create(validated_data)

    def to_representation(self, instance):
        recipe_data = RecipeMinifiedSerializer(
            instance.recipe,
            context=self.context,
        ).data
        return recipe_data
