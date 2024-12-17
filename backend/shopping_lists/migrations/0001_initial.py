# Generated by Django 5.1.3 on 2024-12-03 08:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("recipes", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ShoppingList",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shopping_lists",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "recipes",
                    models.ManyToManyField(
                        related_name="shopping_lists", to="recipes.recipe"
                    ),
                ),
            ],
        ),
    ]
