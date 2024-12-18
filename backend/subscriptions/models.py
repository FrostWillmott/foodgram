from django.db import models


class Subscription(models.Model):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    author = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="subscribers",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"],
                name="unique_subscription",
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="prevent_self_subscription",
            ),
        ]

    def __str__(self):
        return f"{self.user} {self.author}"
