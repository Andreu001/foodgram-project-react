from django_filters import rest_framework as filter
from rest_framework.filters import SearchFilter
from recipes.models import Recipe, Tag


class IngredientFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(filter.FilterSet):
    author = filter.CharFilter()
    tags = filter.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        label='Tags',
        to_field_name='slug'
    )
    is_favorited = filter.BooleanFilter(
        method='get_favorite'
    )
    is_in_shopping_cart = filter.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def get_is_in_shopping_cart(self, queryset, name, value):
        return self._get_queryset(queryset, name, value, 'shopping_list')

    def get_favorite(self, queryset, name, value):
        return self._get_queryset(queryset, name, value, 'favoriteslist')

    def _get_queryset(self, queryset, name, value, key):
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(**{f'{key}__user': self.request.user})
        return queryset
