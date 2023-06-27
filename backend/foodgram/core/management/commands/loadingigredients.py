# import os
import csv
import logging.config

from recipes.models import Ingredients
from django.core.management import BaseCommand
# from foodgram.settings import BASE_DIR


class Command(BaseCommand):
    help = 'Загрузка ингредиентов'

    def handle(self, *args, **kwargs):
        with open('data/ingredients.csv',
                  encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    Ingredients(name=row[0],
                                units_of_measurement=row[1]).save()
                except Exception as exc:
                    logging.error(exc)

        return logging.info('Загружено')
