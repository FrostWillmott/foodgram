# Generated by Django 5.1.3 on 2024-12-13 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="ingredient",
            options={"ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="recipe",
            name="is_favorited",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="recipe",
            name="is_in_shopping_cart",
            field=models.BooleanField(default=False),
        ),
    ]
