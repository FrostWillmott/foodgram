import os
from datetime import timedelta
from pathlib import Path

import environ
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env()


SECRET_KEY = os.getenv("SECRET_KEY", get_random_secret_key())

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

CSRF_TRUSTED_ORIGINS = ["https://kittygram.biz"]

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

AUTH_USER_MODEL = "users.User"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "djoser",
    "django_filters",
    "api.apps.ApiConfig",
    "favorites.apps.FavoritesConfig",
    "recipes.apps.RecipesConfig",
    "shopping_lists.apps.ShoppingListsConfig",
    "subscriptions.apps.SubscriptionsConfig",
    "users.apps.UsersConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "foodgram_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "foodgram_backend.wsgi.application"

DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        # "ENGINE": "django.db.backends.postgresql",
        # "NAME": os.environ.get("POSTGRES_DB", "postgres"),
        # "USER": os.environ.get("POSTGRES_USER", "postgres"),
        # "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        # "HOST": os.environ.get("DB_HOST", "db"),
        # "PORT": os.environ.get("DB_PORT", "5432"),
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

MEDIA_URL = "/media/"
# MEDIA_ROOT = "/media"
MEDIA_ROOT = BASE_DIR / "media"

STATIC_URL = "static/"
STATIC_ROOT = "/backend_static/static"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

DJOSER = {
    "LOGIN_FIELD": "email",
    "SEND_ACTIVATION_EMAIL": False,
    "PERMISSIONS": {
        "recipe_list": ("api.v1.permissions.AuthorStaffOrReadOnly",),
        "user": ("api.v1.permissions.OwnerUserOrReadOnly",),
        "user_list": ("api.v1.permissions.OwnerUserOrReadOnly",),
        "user_delete": ("rest_framework.permissions.IsAuthenticated",),
        "me": ("rest_framework.permissions.IsAuthenticated",),
        "current_user": ("rest_framework.permissions.IsAuthenticated",),
        "avatar": ("rest_framework.permissions.IsAuthenticated",),
    },
    "SERIALIZERS": {
        "user": "api.v1.serializers.UserSerializer",
        "current_user": "api.v1.serializers.UserSerializer",
        "avatar": "api.v1.serializers.AvatarSerializer",
    },
    "ACTIVATION_URL": "auth/login/",
}

DEFAULT_FROM_EMAIL = "no-reply@example.com"
