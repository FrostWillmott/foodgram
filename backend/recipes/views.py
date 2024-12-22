from django.shortcuts import redirect
from rest_framework.generics import get_object_or_404

from recipes.models import Recipe


def shortlink_redirect_view(request, short_link):
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return redirect(f"/recipes/{recipe.id}/")
