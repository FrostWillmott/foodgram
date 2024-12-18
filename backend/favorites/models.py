from django.db import models


class Favorite(models.Model):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="shopping_cart",
    )
    recipe = models.ForeignKey(
        "recipes.Recipe",
        on_delete=models.CASCADE,
        related_name="favorites",
    )

    class Meta:
        unique_together = ("user", "recipe")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_favorite",
            ),
        ]

    def __str__(self):
        return f"{self.user} {self.recipe}"
