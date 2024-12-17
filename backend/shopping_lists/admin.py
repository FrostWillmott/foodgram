from django.contrib import admin

from shopping_lists.models import ShoppingCart


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__email')
    list_display = ('user', 'recipe')
