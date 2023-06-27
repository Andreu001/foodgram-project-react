from django.contrib import admin

from .models import (FavoritesList, Ingredients, Follow,
                     Recipe, ShoppingList, Tag)


class IngredientsRecipeLine(admin.TabularInline):
    """ Связь  ингридиентов в рецепте """
    model = Recipe.ingredients.through


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    """ Админ панель управление ингридиентами """
    list_display = ('name', 'units_of_measurement')
    search_fields = ('name', )
    list_filter = ('name', )
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """ Админ панель управление рецептами """
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
    """ Админ панель управление подписками """
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
