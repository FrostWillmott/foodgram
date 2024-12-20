from django.conf import settings
from django.db import models

from recipes.models import Recipe


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="in_carts",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_carts",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_user_recipe"
            ),
        ]

    def __str__(self):
        return f"{self.user.username}'s cart item: {self.recipe.name}"
