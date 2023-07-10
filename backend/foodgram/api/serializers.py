from django.conf import settings
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework import serializers

from recipes.models import (FavoritesList, Follow, Ingredients,
                            IngredientInRecipe, Recipe, Tag, ShoppingList)
from users.models import User


class CustomUserCreateSerializer(UserCreateSerializer):
    """ Сериализатор создания пользователя. """
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name',
                  'last_name', 'password'
                  )


class CustomUserSerializer(UserSerializer):
    """ Сериализатор модели пользователя. """
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed'
                  )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return request is not None and (
            request.user.is_authenticated and Follow.objects.filter(
                user=request.user, author=obj
            ).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра тегов"""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор связи ингридиентов и рецепта"""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор для просмотра рецепта"""
    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited')
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time'
                  )

    def get_ingredients(self, obj):
        ingredients = IngredientInRecipe.objects.filter(recipe=obj)
        return IngredientRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return request is not None and (
            request.user.is_authenticated and FavoritesList.objects.filter(
                user=request.user, recipe__id=obj.id).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return request is not None and (
            request.user.is_authenticated and ShoppingList.objects.filter(
                user=request.user, recipe__id=obj.id).exists())


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор добавление ингридиентов в рецепт """
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор  создания, редактирования и удаления рецепта"""
    author = CustomUserSerializer(read_only=True)
    ingredients = AddIngredientRecipeSerializer(many=True)
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'tags',
                  'image', 'name', 'text', 'cooking_time'
                  )

    def create_ingredients(self, ingredients, recipe):
        IngredientInRecipe.objects.bulk_create(
            [IngredientInRecipe(
                ingredient=Ingredients.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    @transaction.atomic
    def create(self, validated_data):
        """ Создание рецепта """
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(
            author=author, **validated_data
        )
        self.create_ingredients(recipe=recipe, ingredients=ingredients)
        recipe.tags.set(tags)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """ Изменение рецепта """
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_ingredients(recipe=instance,
                                ingredients=ingredients
                                )
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class RecipeShortInfo(serializers.ModelSerializer):
    """ Сериализатор отображения избранного """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingListSerializer(serializers.ModelSerializer):
    """ Сериализатор списка покупок """
    class Meta:
        model = ShoppingList
        fields = ('recipe', 'user')

    def validate(self, data):
        request = self.context.get('request')
        recipe = data['recipe']
        if ShoppingList.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            raise ValidationError({
                'errors': 'Рецепт уже есть в корзине.'
            })
        return data

    def to_representation(self, instance):
        return RecipeShortInfo(instance.recipe, context={
            'request': self.context.get('request')
        }).data


class FavoriteSerializer(serializers.ModelSerializer):
    """ Сериализатор избранного """
    class Meta:
        model = FavoritesList
        fields = ('user', 'recipe')

    def validate(self, data):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False

    def to_representation(self, instance):
        return RecipeShortInfo(instance.recipe, context={
            'request': self.context.get('request')
        }).data


class FollowSerializer(CustomUserSerializer):
    """ Сериализатор подписки"""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        model = User
        fields = CustomUserSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )
        read_only_fields = '__all__',

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        limit = request.query_params.get('recipes_limit',
                                         settings.RECIPES_LIMIT)
        recipes = obj.recipes.select_related('author').all[:int(limit)]
        serializer = RecipeShortInfo(recipes, many=True, read_only=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
