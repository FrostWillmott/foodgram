import random
import string

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User
from .constants import (
    MAX_AMOUNT,
    MAX_COOKING_TIME,
    MAX_LENGTH_INGRIDIENT_NAME,
    MAX_LENGTH_MEASUREMENT_UNIT,
    MAX_LENGTH_SHORT_LINK,
    MAX_LENGTH_SLUG,
    MAX_LENGTH_TAG_NAME,
    MAX_RECIPE_NAME,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
)


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_INGRIDIENT_NAME)
    measurement_unit = models.CharField(max_length=MAX_LENGTH_MEASUREMENT_UNIT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_name_measurement_unit",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"Ingredient: {self.name} ({self.measurement_unit})"


class Tag(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_TAG_NAME)
    slug = models.SlugField(max_length=MAX_LENGTH_SLUG, unique=True)

    def __str__(self):
        return f"Tag: {self.name} (slug: {self.slug})"


class Recipe(models.Model):
    name = models.CharField(max_length=MAX_RECIPE_NAME)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
    )
    image = models.ImageField(upload_to="recipes/images/")
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message="Cooking time must be"
                        f" at least {MAX_LENGTH_SHORT_LINK} minute.",
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message="Cooking time must not"
                        f" exceed {MAX_COOKING_TIME} minutes.",
            ),
        ],
    )
    tags = models.ManyToManyField(Tag, related_name="recipes")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
    )
    short_link = models.CharField(
        max_length=MAX_LENGTH_SHORT_LINK,
        unique=True,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"Recipe: {self.name} by {self.author.username}"

    def generate_short_link(self):
        """Generate a unique short link."""
        while True:
            short_link = "".join(
                random.choices(string.ascii_letters + string.digits, k=6),
            )
            if not Recipe.objects.filter(short_link=short_link).exists():
                return short_link

    def save(self, *args, **kwargs):
        """Override save method to generate short link on creation."""
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_AMOUNT,
                message="Cooking time must be"
                        f" at least {MAX_LENGTH_SHORT_LINK} minute.",
            ),
            MaxValueValidator(
                MAX_AMOUNT,
                message="Cooking time must not"
                        f" exceed {MAX_COOKING_TIME} minutes.",
            ),
        ],
    )

    def __str__(self):
        return (
            f"{self.amount} {self.ingredient.measurement_unit}"
            f" of {self.ingredient.name}"
        )
