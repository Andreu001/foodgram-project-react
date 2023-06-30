from django.contrib import admin

from .models import (FavoritesList, Ingredients, Follow,
                     Recipe, ShoppingList, Tag)


class IngredientsRecipeLine(admin.TabularInline):
    """ Связь  ингридиентов в рецепте """
    model = Recipe.ingredients.through


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    """ Управление ингридиентами """
    list_display = ('name', 'measurement_unit')
    search_fields = ('name', )
    list_filter = ('name', )
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Управление тегами"""
    list_display = ('name', 'color', 'slug',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """ Управление рецептами """
    list_display = ('name', 'author', 'favorites')
    search_fields = ('author', 'name')
    list_filter = ('tags', )
    filter_horizontal = ('tags', )
    empty_value_display = '-пусто-'
    inlines = (IngredientsRecipeLine,)

    def favorites(self, obj):
        if FavoritesList.objects.filter(recipe=obj).exists():
            return FavoritesList.objects.filter(recipe=obj).count()
        return 0

    favorites.short_description = 'Количество добавлений рецепта в избранное'


@admin.register(FavoritesList)
class FavoriteAdmin(admin.ModelAdmin):
    """ Управление подписками """
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = '-пусто-'


@admin.register(ShoppingList)
class ShoppingCartAdmin(admin.ModelAdmin):
    """ Админ панель списка покупок """
    list_display = ('recipe', 'user')
    list_filter = ('recipe', 'user')
    search_fields = ('user', )
    empty_value_display = '-пусто-'


@admin.register(Follow)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('user', 'author',)
