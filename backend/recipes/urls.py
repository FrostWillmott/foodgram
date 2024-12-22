from django.urls import path

from recipes.views import shortlink_redirect_view

urlpatterns = [
    path("<str:short_link>", shortlink_redirect_view, name="recipe-shortlink"),
]
