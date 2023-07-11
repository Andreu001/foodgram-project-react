import csv
import logging.config

from recipes.models import Ingredients
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Загрузка ингредиентов'

    def handle(self, *args, **kwargs):
        with open('data/ingredients.csv',
                  encoding='utf-8') as f:
            reader = csv.reader(f)
            ingredients = []
            Ingredients.objects.bulk_create(ingredients)
            for row in reader:
                ingredients.append(
                    Ingredients(name=row[0], measurement_unit=row[1])
                )
            Ingredients.objects.bulk_create(ingredients)

        return logging.info('Загружено')
