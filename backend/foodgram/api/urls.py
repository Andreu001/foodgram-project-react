from django.urls import include, path
from rest_framework import routers


from .views import (
                IngredientsViewSet,
                RecipeViewSet,
                TagViewSet,
                UsersViewSet
            )

app_name = 'api'

router = routers.DefaultRouter()

router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientsViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'users', UsersViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),

]
