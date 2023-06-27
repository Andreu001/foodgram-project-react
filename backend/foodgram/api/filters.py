from django_filters import rest_framework as filters
from recipes.models import Recipe, Tag, Ingredients


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
    )

    class Meta:
        model = Ingredients
        fields = '__all__'


class RecipeFilter(filters.FilterSet):
    author = filters.CharFilter()
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        label='Tags',
        to_field_name='slug'
    )
    is_favorited = filters.BooleanFilter(
        method='get_favorite'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author')
