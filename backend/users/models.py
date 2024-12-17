from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from .constants import (

    MAX_LENGTH_NAME,
    MAX_LENGTH_USERNAME,

)
from .managers import CustomUserManager
from .validators import forbidden_username_validator


class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = 'email'
    email = models.EmailField(
        unique=True,
        blank=False
    )
    username = models.CharField(
        "Имя пользователя",
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        validators=(
            UnicodeUsernameValidator(),
            forbidden_username_validator,
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
        upload_to='users/avatars/',
        blank=True,
        null=True,
    )

    password = models.CharField(
        max_length=128,
        blank=False,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username