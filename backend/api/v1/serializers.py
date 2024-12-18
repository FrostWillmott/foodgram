import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    CharField,
    EmailField,
    ImageField,
    IntegerField,
    SerializerMethodField,
)
from rest_framework.serializers import ModelSerializer, Serializer
from subscriptions.models import Subscription

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Serializer for custom user model."""

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
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()

    def get_recipes_count(self, obj):
        """Get the count of recipes authored by the given user."""
        return Recipe.objects.filter(author=obj.author).count()

    def get_avatar(self, obj):
        """Get the URL of the user's avatar."""
        if obj.avatar:
            return obj.avatar.url
        return None


class Base64imageField(ImageField):
    """Custom image field to handle base64 encoded images."""

    def to_internal_value(self, data):
        """Convert base64 encoded image data to a Django ContentFile."""
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f"temp.{ext}")
        return super().to_internal_value(data)


class AvatarSerializer(ModelSerializer):
    """Serializer for user avatar."""

    avatar = Base64imageField(allow_null=True)

    class Meta:
        model = User
        fields = ["avatar"]


class SubscriptionSerializer(ModelSerializer):
    """Serializer for user subscriptions."""

    is_subscribed = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ("user", "author", "is_subscribed", "recipes_count")
        extra_kwargs = {
            "user": {"read_only": True},
            "author": {"read_only": True},
        }

    def get_is_subscribed(self, obj):
        """Check if the user is subscribed to the author."""
        return Subscription.objects.filter(
            user=obj.user,
            author=obj.author,
        ).exists()

    def get_recipes_count(self, obj):
        """Get the count of recipes authored by the subscription's author."""
        return Recipe.objects.filter(author=obj.author).count()


class TagSerializer(ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class IngredientInRecipeReadSerializer(ModelSerializer):
    """Serializer for reading ingredients in a recipe."""

    id = IntegerField(source="ingredient.id")
    name = CharField(source="ingredient.name", read_only=True)
    measurement_unit = CharField(
        source="ingredient.measurement_unit", read_only=True
    )
    amount = IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ["id", "name", "measurement_unit", "amount"]


class IngredientInRecipeWriteSerializer(ModelSerializer):
    """Serializer for writing ingredients in a recipe."""

    id = IntegerField()
    amount = IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ["id", "amount"]


class RecipeReadSerializer(ModelSerializer):
    """Serializer for reading recipes."""

    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    ingredients = IngredientInRecipeReadSerializer(
        many=True, source="recipeingredient_set"
    )
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = [
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
        ]
        read_only_fields = ["author"]

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
    image = Base64imageField()

    class Meta:
        model = Recipe
        fields = [
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        ]
        read_only_fields = ["author"]

    def validate_ingredients(self, value):
        """Validate the ingredients field."""
        if not value:
            raise ValidationError("Ingredients field cannot be empty.")
        ingredient_ids = set()
        for ingredient_data in value:
            if ingredient_data["amount"] < 1:
                raise ValidationError("Ingredient amount must be at least 1.")
            if ingredient_data["id"] in ingredient_ids:
                raise ValidationError("Duplicate ingredients are not allowed.")
            ingredient_ids.add(ingredient_data["id"])
            try:
                Ingredient.objects.get(id=ingredient_data["id"])
            except Ingredient.DoesNotExist:
                raise ValidationError(
                    f"Ingredient with id {ingredient_data['id']} does not exist."
                )
        return value

    def validate_tags(self, value):
        """Validate the tags field."""
        if len(value) != len(set(value)):
            raise ValidationError("Duplicate tags are not allowed.")
        return value

    def validate_cooking_time(self, value):
        """Validate the cooking time field."""
        if value < 1:
            raise ValidationError("Cooking time must be at least 1 minute.")
        return value

    def create(self, validated_data):
        """Create a new recipe."""
        ingredients_data = validated_data.pop("ingredients")
        tags = validated_data.pop("tags", [])
        recipe = Recipe.objects.create(
            author=self.context["request"].user, **validated_data
        )
        recipe.tags.set(tags)
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data["id"])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data["amount"],
            )
        return recipe

    def update(self, instance, validated_data):
        """Update an existing recipe."""
        ingredients_data = validated_data.pop("ingredients", None)
        tags = validated_data.pop("tags", None)

        if ingredients_data is None or len(ingredients_data) == 0:
            raise ValidationError(
                {"ingredients": "This field cannot be empty or missing."}
            )

        if tags is None or len(tags) == 0:
            raise ValidationError(
                {"tags": "This field cannot be empty or missing."}
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.tags.set(tags)
        instance.ingredients.clear()

        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data["id"])
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient,
                amount=ingredient_data["amount"],
            )

        return instance


class IngredientSerializer(Serializer):
    """Serializer for ingredients."""

    id = IntegerField()
    name = CharField()
    measurement_unit = CharField()

    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]


class AuthorSerializer(Serializer):
    """Serializer for authors."""

    id = IntegerField()
    username = CharField()
    email = EmailField()


class RecipeMinifiedSerializer(ModelSerializer):
    """Serializer for a minified version of recipes."""

    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]


class UserWithRecipesSerializer(ModelSerializer):
    """Serializer for users with their recipes."""

    is_subscribed = SerializerMethodField()
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()
    avatar = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        ]

    def get_is_subscribed(self, obj):
        """Check if the authenticated user is subscribed to the given user."""
        user = self.context["request"].user
        return Subscription.objects.filter(user=user, author=obj).exists()

    def get_recipes(self, obj):
        """Get the recipes authored by the given user."""
        recipes_limit = self.context["request"].query_params.get(
            "recipes_limit"
        )
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Get the count of recipes authored by the given user."""
        return Recipe.objects.filter(author=obj).count()

    def get_avatar(self, obj):
        """Get the URL of the user's avatar."""
        if obj.avatar:
            return obj.avatar.url
        return None
