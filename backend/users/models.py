from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from .constants import (
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_NAME,
    MAX_LENGTH_USERNAME,
)


class User(AbstractUser):
    USERNAME_FIELD = "email"
    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
        blank=False,
    )
    username = models.CharField(
        "Имя пользователя",
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        validators=(
            UnicodeUsernameValidator(),
        ),
    )
    first_name = models.CharField(
        "Имя",
        max_length=MAX_LENGTH_NAME,
        blank=False,
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=MAX_LENGTH_NAME,
        blank=False,
    )

    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
    )

    password = models.CharField(
        max_length=128,
        blank=False,
    )

    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username
