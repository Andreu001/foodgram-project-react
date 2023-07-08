from datetime import datetime
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.http import HttpResponse
from djoser.views import UserViewSet
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from users.models import User
from recipes.models import (FavoritesList, Ingredients, IngredientInRecipe,
                            Recipe, ShoppingList, Tag, Follow
                            )

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .pagination import CatsPagination
from .serializers import (CreateRecipeSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeSerializer,
                          ShoppingListSerializer, TagSerializer,
                          FollowSerializer, CustomUserSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Получить список всех категорий"""
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (IngredientFilter,)
    search_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """ Операции с рецептами """
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly | IsAdminOrReadOnly,)
    pagination_class = CatsPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return CreateRecipeSerializer

    @staticmethod
    def post_method_for_actions(request, pk, serializers):
        """ Метод добавления """
        data = {'user': request.user.id, 'recipe': pk}
        serializer = serializers(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_method_for_actions(request, pk, model):
        """ Метод удаления """
        obj = model.objects.filter(user=request.user, recipe__id=pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def shopping_cart(self, request, pk):
        """ Добавить в список покупок """
        return self.post_method_for_actions(
            request, pk, serializers=ShoppingListSerializer
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """ Удалить из списка покупок """
        return self.delete_method_for_actions(
            request=request, pk=pk, model=ShoppingList)

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk):
        """ Добавить в избранное """
        return self.post_method_for_actions(
            request=request, pk=pk, serializers=FavoriteSerializer)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """ Удалить из избранного """
        return self.delete_method_for_actions(
            request=request, pk=pk, model=FavoritesList)

    @action(
        detail=False, methods=['get'], permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """ Скачать рецепт """
        user = request.user
        if not user.shopping_list.exists():
            return Response(status=HTTP_400_BAD_REQUEST)

        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_list__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        today = datetime.today()
        shopping_list = (
            f'Список покупок для: {user.get_full_name()}\n\n'
            f'Дата: {today:%Y-%m-%d}\n\n'
        )
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]}'
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        shopping_list += f'\n\nFoodgram ({today:%Y})'

        filename = f'{user.username}_shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response


class UsersViewSet(UserViewSet):
    """ Отображение подписок """
    pagination_class = CatsPagination
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    @action(
        url_name='subscribe',
        url_path='subscribe',
        detail=True,
        methods=['post', 'delete'],
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        user = request.user
        if request.method == 'POST':
            Follow.objects.create(user=user, author=author)
            queryset = User.objects.filter(subscribing__user=user)
            pages = self.paginate_queryset(queryset)
            serializer = FollowSerializer(pages,
                                          many=True,
                                          context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = get_object_or_404(Follow,
                                             user_id=request.user,
                                             author_id=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False)
    def subscriptions(self, request):
        """ Отоброжение подписок """
        subscriptions_list = self.paginate_queryset(
            User.objects.filter(subscribing__user=request.user)
        )
        serializer = FollowSerializer(
            subscriptions_list, many=True, context={
                'request': request
            }
        )
        return self.get_paginated_response(serializer.data)
