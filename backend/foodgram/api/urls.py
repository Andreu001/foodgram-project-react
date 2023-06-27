from django.urls import include, path
from rest_framework import routers

from .views import IngredientsViewSet, RecipeViewSet, TagViewSet

app_name = 'api'

router = routers.DefaultRouter()

router.register('recipes', RecipeViewSet)
router.register('ingredients', IngredientsViewSet)
router.register('tags', TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
