from datetime import datetime
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from djoser.views import UserViewSet
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from recipes.models import (Ingredients, Recipe, FavoritesList, Follow,
                            ShoppingList, IngredientInRecipe, Tag
                            )
from .permissions import IsAdminOrReadOnly
from users.models import User
from .pagination import CatsPagination
from .serializers import (CreateRecipeSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeSerializer,
                          ShoppingListSerializer, TagSerializer,
                          FollowListSerializer, FollowSerializer)
from .filters import RecipeFilter, IngredientFilter


class UsersViewSet(UserViewSet):
    """ Отображение подписок/подписться/отписаться """
    pagination_class = CatsPagination

    @action(['get'], detail=False, permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(methods=['get'], detail=False)
    def subscriptions(self, request):
        """ Отоброжение подписок """
        subscriptions_list = self.paginate_queryset(
            User.objects.filter(following__user=request.user)
        )
        serializer = FollowListSerializer(
            subscriptions_list, many=True, context={
                'request': request
            }
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True)
    def subscribe(self, request, id):
        """ Подписаться/отписаться """
        if request.method == 'POST':
            serializer = FollowSerializer(
                data={
                    'user': request.user.id,
                    'author': get_object_or_404(User, id=id).id
                },
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscription = get_object_or_404(
            Follow,
            author=get_object_or_404(User, id=id),
            user=request.user
        )
        self.perform_destroy(subscription)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Получить список всех категорий. Права доступа: Доступно без токена
    """
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (IngredientFilter)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """ Операции с рецептами: добавление/изменение/удаление/просмотр. """
    queryset = Recipe.objects.all()
    permission_classes = (AllowAny, )
    pagination_class = CatsPagination
    filter_backends = (DjangoFilterBackend, )
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
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепт уже удален!'},
                        status=status.HTTP_400_BAD_REQUEST)

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
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        shopping_list += f'\n\nFoodgram ({today:%Y})'

        filename = f'{user.username}_shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
